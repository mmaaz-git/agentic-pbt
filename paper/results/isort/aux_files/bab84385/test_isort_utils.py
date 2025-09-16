import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st
from hypothesis import settings
import isort.utils


# Strategy for valid filesystem paths (avoiding problematic characters)
path_component = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="/\\:*?\"<>|"),
    min_size=1, 
    max_size=20
).filter(lambda s: s not in (".", "..", "~"))

def path_strategy():
    """Generate valid filesystem paths."""
    return st.lists(path_component, min_size=1, max_size=5).map(lambda parts: "/" + "/".join(parts))

# Strategy for config data
config_data_strategy = st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=0,
    max_size=5
)


class TestTrie:
    """Test properties of the Trie class."""
    
    @given(
        config_file=path_strategy(),
        config_data=config_data_strategy
    )
    def test_trie_insert_search_roundtrip(self, config_file, config_data):
        """Property: After inserting a config, searching for files in that directory should return it."""
        trie = isort.utils.Trie()
        
        # Insert the config
        trie.insert(config_file, config_data)
        
        # Search for a file in the same directory as the config
        search_path = str(Path(config_file).parent / "test_file.py")
        found_config_file, found_config_data = trie.search(search_path)
        
        # The found config should match what we inserted
        assert found_config_file == config_file
        assert found_config_data == config_data
    
    @given(
        parent_config=path_strategy(),
        parent_data=config_data_strategy,
        child_subpath=st.lists(path_component, min_size=1, max_size=3),
        child_file=path_component
    )
    def test_trie_nearest_parent_config(self, parent_config, parent_data, child_subpath, child_file):
        """Property: Search returns the nearest parent config when no exact match exists."""
        trie = isort.utils.Trie()
        
        # Insert parent config
        trie.insert(parent_config, parent_data)
        
        # Search for a file in a subdirectory (which doesn't have its own config)
        parent_dir = Path(parent_config).parent
        child_path = parent_dir / Path(*child_subpath) / f"{child_file}.py"
        
        found_config_file, found_config_data = trie.search(str(child_path))
        
        # Should find the parent config
        assert found_config_file == parent_config
        assert found_config_data == parent_data
    
    @given(
        configs=st.lists(
            st.tuples(path_strategy(), config_data_strategy),
            min_size=2,
            max_size=5,
            unique_by=lambda x: x[0]
        )
    )
    def test_trie_multiple_configs_hierarchy(self, configs):
        """Property: With multiple configs, search returns the most specific (deepest) matching config."""
        trie = isort.utils.Trie()
        
        # Insert all configs
        for config_file, config_data in configs:
            trie.insert(config_file, config_data)
        
        # For each config, files in its directory should find that config
        for config_file, config_data in configs:
            search_path = str(Path(config_file).parent / "test.py")
            found_file, found_data = trie.search(search_path)
            
            # Find the most specific config that should match this path
            matching_configs = []
            search_parts = Path(search_path).resolve().parts
            
            for cf, cd in configs:
                config_parts = Path(cf).parent.resolve().parts
                if len(config_parts) <= len(search_parts):
                    if all(cp == sp for cp, sp in zip(config_parts, search_parts[:len(config_parts)])):
                        matching_configs.append((cf, cd, len(config_parts)))
            
            if matching_configs:
                # Should find the deepest matching config
                expected = max(matching_configs, key=lambda x: x[2])
                assert found_file == expected[0]
                assert found_data == expected[1]
    
    @given(st.data())
    def test_trie_empty_search(self, data):
        """Property: Searching in an empty trie returns empty results."""
        trie = isort.utils.Trie()
        
        search_path = data.draw(path_strategy())
        found_file, found_data = trie.search(search_path)
        
        assert found_file == ""
        assert found_data == {}


class TestExistsCaseSensitive:
    """Test properties of the exists_case_sensitive function."""
    
    @given(
        dirname=path_component,
        basename=st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=122, blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=20
        ).filter(lambda s: s.strip() and s not in (".", "..")),
        use_different_case=st.booleans()
    )
    @settings(max_examples=100)
    def test_exists_case_sensitive_on_real_files(self, dirname, basename, use_different_case):
        """Property: exists_case_sensitive correctly handles case sensitivity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory
            subdir = Path(tmpdir) / dirname
            subdir.mkdir(exist_ok=True)
            
            # Create a file with specific case
            actual_file = subdir / basename
            actual_file.write_text("test content")
            
            # Test with exact case - should always return True
            assert isort.utils.exists_case_sensitive(str(actual_file)) is True
            
            if use_different_case and basename != basename.upper() and basename != basename.lower():
                # Test with different case
                if sys.platform.startswith("win") or sys.platform == "darwin":
                    # On Windows/macOS, the file might exist but case matters for imports
                    wrong_case_file = subdir / basename.swapcase()
                    result = isort.utils.exists_case_sensitive(str(wrong_case_file))
                    
                    # On case-insensitive filesystems, os.path.exists returns True
                    # but exists_case_sensitive should check actual case
                    if os.path.exists(str(wrong_case_file)):
                        # The function should detect case mismatch
                        assert result is False
                else:
                    # On Linux (case-sensitive), wrong case means file doesn't exist
                    wrong_case_file = subdir / basename.swapcase()
                    assert isort.utils.exists_case_sensitive(str(wrong_case_file)) is False
    
    @given(
        path=path_strategy()
    )
    def test_exists_case_sensitive_nonexistent(self, path):
        """Property: Returns False for paths that don't exist."""
        # Create a path that definitely doesn't exist
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "definitely_does_not_exist" / path.lstrip("/")
            assert isort.utils.exists_case_sensitive(str(nonexistent)) is False
    
    @given(
        filename=path_component
    )
    def test_exists_case_sensitive_cache_consistency(self, filename):
        """Property: Due to lru_cache, repeated calls return consistent results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / filename
            
            # First check - file doesn't exist
            result1 = isort.utils.exists_case_sensitive(str(filepath))
            result2 = isort.utils.exists_case_sensitive(str(filepath))
            assert result1 == result2 == False
            
            # Create the file
            filepath.write_text("content")
            
            # Due to caching, might still return False (this tests cache behavior)
            # Clear cache to test fresh
            isort.utils.exists_case_sensitive.cache_clear()
            
            # Now should return True
            result3 = isort.utils.exists_case_sensitive(str(filepath))
            result4 = isort.utils.exists_case_sensitive(str(filepath))
            assert result3 == result4 == True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])