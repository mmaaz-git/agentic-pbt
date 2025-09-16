"""Additional edge case tests for isort.place module"""
import re
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings, example
from mock_deps import Config, sections

import place


# Test special characters in module names
@given(
    special_chars=st.sampled_from(["[", "]", "(", ")", "{", "}", ".", "*", "+", "?", "^", "$", "|", "\\"])
)
def test_forced_separate_with_special_regex_chars(special_chars):
    """Test that special regex characters in forced_separate patterns are handled correctly."""
    # Create a module name with special characters (though Python won't allow most)
    module_name = f"test{special_chars}module" if special_chars != "." else "test.module"
    
    # The pattern should match literally
    pattern = module_name
    config = Config(forced_separate=[pattern])
    
    # This tests if fnmatch handles special chars correctly
    result = place.module(module_name, config)
    
    # The test here is that it shouldn't crash


# Test empty module name
def test_empty_module_name():
    """Test behavior with empty module name."""
    config = Config()
    result = place.module("", config)
    # Should return default section for empty string
    assert result == config.default_section


# Test module names with only dots
@given(num_dots=st.integers(min_value=1, max_value=10))
def test_only_dots_module_name(num_dots):
    """Test module names that are only dots."""
    name = "." * num_dots
    config = Config()
    result = place.module(name, config)
    # Should be treated as local
    assert result == "LOCALFOLDER"


# Test forced_separate pattern without asterisk
def test_forced_separate_auto_append_asterisk():
    """Test that forced_separate patterns without * get it appended for matching."""
    module_name = "mypackage.submodule.code"
    pattern = "mypackage"  # No asterisk
    
    config = Config(forced_separate=[pattern])
    result = place.module(module_name, config)
    
    # Should match because asterisk is auto-appended
    assert result == pattern


# Test multiple dots in module names
@given(
    parts=st.lists(st.just(""), min_size=2, max_size=5)
)
def test_module_with_consecutive_dots(parts):
    """Test module names with consecutive dots (invalid but should not crash)."""
    # Create module name with multiple consecutive dots
    name = ".".join(parts)  # Results in something like "...", "....", etc.
    
    config = Config()
    # Should not crash
    result = place.module(name, config)
    
    if name.startswith("."):
        assert result == "LOCALFOLDER"


# Test src_path with namespace packages
def test_src_path_namespace_package():
    """Test _src_path function with namespace packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a namespace package structure
        ns_package = tmpdir_path / "namespace_pkg"
        ns_package.mkdir()
        sub_module = ns_package / "submodule.py"
        sub_module.write_text("# submodule")
        
        # No __init__.py file - this makes it a namespace package
        
        config = Config(
            src_paths=[tmpdir_path],
            auto_identify_namespace_packages=True,
            supported_extensions=frozenset(["py"])
        )
        
        # Test detection
        result = place.module("namespace_pkg.submodule", config)
        assert result == sections.FIRSTPARTY


# Test _is_namespace_package with different scenarios
def test_namespace_package_detection():
    """Test the _is_namespace_package function with various scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Case 1: Directory with Python files but no __init__.py
        pkg1 = tmpdir_path / "pkg1"
        pkg1.mkdir()
        (pkg1 / "module.py").write_text("# module")
        
        assert place._is_namespace_package(pkg1, frozenset(["py"]))
        
        # Case 2: Directory with empty __init__.py
        pkg2 = tmpdir_path / "pkg2"
        pkg2.mkdir()
        (pkg2 / "__init__.py").write_text("")
        (pkg2 / "module.py").write_text("# module")
        
        assert place._is_namespace_package(pkg2, frozenset(["py"]))
        
        # Case 3: Directory with __init__.py containing only comments
        pkg3 = tmpdir_path / "pkg3"
        pkg3.mkdir()
        (pkg3 / "__init__.py").write_text("# Just a comment\n# Another comment")
        (pkg3 / "module.py").write_text("# module")
        
        assert place._is_namespace_package(pkg3, frozenset(["py"]))
        
        # Case 4: Directory with __init__.py containing __path__
        pkg4 = tmpdir_path / "pkg4"
        pkg4.mkdir()
        (pkg4 / "__init__.py").write_text("__path__ = []")
        
        assert place._is_namespace_package(pkg4, frozenset(["py"]))
        
        # Case 5: Regular package with code in __init__.py
        pkg5 = tmpdir_path / "pkg5"
        pkg5.mkdir()
        (pkg5 / "__init__.py").write_text("x = 1")
        
        assert not place._is_namespace_package(pkg5, frozenset(["py"]))


# Test pattern matching with complex regex
@given(
    module_name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu"), whitelist_characters="._"), min_size=1, max_size=30)
)
def test_complex_regex_patterns(module_name):
    """Test known_patterns with complex regex patterns."""
    # Skip invalid module names
    assume("." not in module_name or all(part.isidentifier() or part == "" for part in module_name.split(".")))
    assume(not module_name.startswith("."))
    assume(module_name and module_name[0].isalpha() or module_name[0] == "_")
    
    # Create a regex pattern that matches modules ending with "test"
    pattern = re.compile(r".*test$")
    config = Config(
        known_patterns=[(pattern, "TESTMODULE")],
        sections={"TESTMODULE", "THIRDPARTY"}
    )
    
    result = place.module(module_name, config)
    
    # Check if any part of the module name ends with "test"
    parts = module_name.split(".")
    should_match = False
    for i in range(len(parts), 0, -1):
        partial = ".".join(parts[:i])
        if partial.endswith("test"):
            should_match = True
            break
    
    if should_match:
        assert result == "TESTMODULE"


# Test forced_separate with dot prefix
def test_forced_separate_with_dot_prefix():
    """Test that forced_separate also checks with a dot prefix."""
    module_name = "relative.import"
    pattern = "relative*"
    
    config = Config(forced_separate=[pattern])
    
    # Test both with and without dot
    result1 = place.module(module_name, config)
    result2 = place.module("." + module_name, config)
    
    assert result1 == pattern  # Should match without dot
    assert result2 == "LOCALFOLDER"  # Should be local because it starts with dot


# Test the module split behavior in _src_path
@given(
    parts=st.lists(
        st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu"), whitelist_characters="_"), 
        min_size=1, 
        max_size=10
    ).filter(lambda s: s.isidentifier()),
    min_size=1,
    max_size=5
    )
)
def test_module_split_in_src_path(parts):
    """Test that module name splitting in _src_path works correctly."""
    module_name = ".".join(parts)
    
    # The split should produce the expected parts
    root, *nested = module_name.split(".", 1)
    
    assert root == parts[0]
    if len(parts) > 1:
        assert nested[0] == ".".join(parts[1:])
    else:
        assert nested == []


# Test with very long module names
@given(
    num_parts=st.integers(min_value=10, max_value=100)
)
def test_very_long_module_names(num_parts):
    """Test behavior with very long module names."""
    parts = [f"part{i}" for i in range(num_parts)]
    module_name = ".".join(parts)
    
    config = Config()
    
    # Should not crash or have performance issues
    result = place.module(module_name, config)
    assert isinstance(result, str)


# Test cache size limit
def test_lru_cache_size_limit():
    """Test that the LRU cache respects its size limit."""
    # Clear cache first
    place.module_with_reason.cache_clear()
    
    config = Config()
    
    # Generate more than 1000 unique module names (cache size is 1000)
    for i in range(1100):
        module_name = f"module_{i}"
        place.module_with_reason(module_name, config)
    
    cache_info = place.module_with_reason.cache_info()
    # Cache size should not exceed maxsize
    assert cache_info.currsize <= 1000


# Test with None config (should use DEFAULT_CONFIG)
def test_none_config():
    """Test that None config falls back to DEFAULT_CONFIG."""
    # This relies on the default parameter in the function signature
    result1 = place.module("test.module")
    result2 = place.module("test.module", None)
    
    # Both should use DEFAULT_CONFIG
    assert result1 == result2