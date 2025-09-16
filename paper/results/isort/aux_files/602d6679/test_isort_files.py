import os
import sys
import tempfile
from pathlib import Path
from typing import List, Set

sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
from isort import files
from isort.settings import Config


# Strategy for generating file paths (mix of valid and invalid)
path_strategy = st.text(
    alphabet=st.characters(blacklist_characters="\x00/\\"),
    min_size=1,
    max_size=50
).map(lambda s: s.strip()).filter(lambda s: s and not s.startswith('.'))


# Strategy for generating lists of paths
paths_strategy = st.lists(path_strategy, min_size=0, max_size=10)


@given(paths_strategy)
@settings(max_examples=500)
def test_broken_paths_property(paths: List[str]):
    """Test that non-existent paths are added to the broken list."""
    config = Config()
    skipped = []
    broken = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create full paths that don't exist
        full_paths = [os.path.join(tmpdir, p) for p in paths]
        
        # Run find
        result = list(files.find(full_paths, config, skipped, broken))
        
        # Property: All paths that don't exist should be in broken
        for path in full_paths:
            if not os.path.exists(path) and not os.path.isdir(path):
                assert path in broken, f"Non-existent path {path} not in broken list"


@given(st.lists(st.text(min_size=1), min_size=0, max_size=5))
@settings(max_examples=100) 
def test_no_duplicate_yields(filenames: List[str]):
    """Test that find doesn't yield duplicate paths."""
    config = Config()
    skipped = []
    broken = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create actual Python files
        created_files = []
        for fname in filenames:
            # Sanitize filename
            safe_name = "".join(c if c.isalnum() or c in '._-' else '_' for c in fname)
            if safe_name and not safe_name.startswith('.'):
                filepath = os.path.join(tmpdir, safe_name + ".py")
                try:
                    with open(filepath, 'w') as f:
                        f.write("# test file\n")
                    created_files.append(filepath)
                except:
                    pass
        
        # Run find on the directory
        result = list(files.find([tmpdir], config, skipped, broken))
        
        # Property: No duplicates in yielded paths
        assert len(result) == len(set(result)), f"Duplicates found in results: {result}"


@given(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10))
@settings(max_examples=100)
def test_skipped_and_broken_only_grow(paths: List[str]):
    """Test that skipped and broken lists only grow, never shrink."""
    config = Config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with multiple calls
        all_skipped = []
        all_broken = []
        
        for i, path in enumerate(paths):
            skipped_before = list(all_skipped)
            broken_before = list(all_broken)
            
            # Create a mix of files and non-existent paths
            if i % 2 == 0:
                full_path = os.path.join(tmpdir, f"file_{i}.py")
                with open(full_path, 'w') as f:
                    f.write("pass\n")
                test_paths = [full_path]
            else:
                test_paths = [os.path.join(tmpdir, f"nonexistent_{i}")]
            
            list(files.find(test_paths, config, all_skipped, all_broken))
            
            # Property: Lists should only grow
            assert len(all_skipped) >= len(skipped_before), "skipped list shrank"
            assert len(all_broken) >= len(broken_before), "broken list shrank"
            
            # Property: Old items should still be present
            for item in skipped_before:
                assert item in all_skipped, f"Item {item} removed from skipped"
            for item in broken_before:
                assert item in all_broken, f"Item {item} removed from broken"


@given(st.lists(st.text(min_size=1, max_size=30).filter(lambda s: s and not s.startswith('.')), 
                 min_size=0, max_size=5))
@settings(max_examples=100)
def test_yielded_files_are_supported_types(filenames: List[str]):
    """Test that all yielded files pass the is_supported_filetype check."""
    config = Config()
    skipped = []
    broken = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with various extensions
        for fname in filenames:
            safe_name = "".join(c if c.isalnum() or c in '._-' else '_' for c in fname)
            if safe_name:
                # Create both .py and non-.py files
                for ext in ['.py', '.txt', '.pyi', '.md', '']:
                    filepath = os.path.join(tmpdir, safe_name + ext)
                    try:
                        with open(filepath, 'w') as f:
                            f.write("test content\n")
                    except:
                        pass
        
        # Run find
        result = list(files.find([tmpdir], config, skipped, broken))
        
        # Property: All yielded files should be supported file types
        for filepath in result:
            assert config.is_supported_filetype(filepath), \
                f"Yielded file {filepath} is not a supported file type"


@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=50)
def test_symlink_cycle_handling(depth: int):
    """Test that find handles symlink cycles without infinite loops."""
    config = Config(follow_links=True)
    skipped = []
    broken = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a directory structure with a symlink cycle
        dirs = []
        for i in range(depth):
            dir_path = os.path.join(tmpdir, f"dir_{i}")
            os.makedirs(dir_path, exist_ok=True)
            dirs.append(dir_path)
            
            # Add a Python file
            with open(os.path.join(dir_path, f"file_{i}.py"), 'w') as f:
                f.write(f"# file {i}\n")
        
        # Create a symlink cycle
        if depth > 1:
            try:
                os.symlink(dirs[0], os.path.join(dirs[-1], "cycle"))
            except:
                # Skip if symlinks not supported
                return
        
        # This should complete without hanging
        result = list(files.find([tmpdir], config, skipped, broken))
        
        # Property: Should find all Python files exactly once
        expected_files = depth  # One .py file per directory
        py_files = [f for f in result if f.endswith('.py')]
        assert len(py_files) == expected_files, \
            f"Expected {expected_files} Python files, found {len(py_files)}"


@given(st.lists(st.sampled_from(['file.py', 'dir/file.py', '../file.py', './file.py']),
                 min_size=1, max_size=10))
@settings(max_examples=100)
def test_find_with_mixed_paths(path_patterns: List[str]):
    """Test find with a mix of files, directories, and relative paths."""
    config = Config()
    skipped = []
    broken = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory for relative path testing
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Create directory structure
            os.makedirs("dir", exist_ok=True)
            os.makedirs("subdir", exist_ok=True)
            
            # Create files based on patterns
            created_files = set()
            test_paths = []
            
            for pattern in path_patterns:
                if '/' in pattern:
                    dirname = os.path.dirname(pattern)
                    if dirname and not dirname.startswith('..'):
                        os.makedirs(dirname, exist_ok=True)
                
                # Only create files that don't go outside tmpdir
                if not pattern.startswith('..'):
                    try:
                        filepath = os.path.abspath(pattern)
                        if filepath.startswith(tmpdir):
                            with open(filepath, 'w') as f:
                                f.write("pass\n")
                            created_files.add(filepath)
                            test_paths.append(pattern)
                    except:
                        test_paths.append(pattern)
                else:
                    test_paths.append(pattern)
            
            # Run find
            result = list(files.find(test_paths, config, skipped, broken))
            
            # Property: All created files should be found (if they're .py files)
            for created in created_files:
                if created.endswith('.py'):
                    assert created in result or any(r == created or os.path.samefile(r, created) 
                                                   for r in result), \
                        f"Created file {created} not found in results"
            
            # Property: No non-existent files in results
            for filepath in result:
                assert os.path.exists(filepath), f"Non-existent file {filepath} in results"
                
        finally:
            os.chdir(original_cwd)