#!/usr/bin/env python3
"""Edge case tests for pathlib - looking for actual bugs."""

import os
import string
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath

import pytest
from hypothesis import assume, given, settings, strategies as st


@given(st.text(min_size=0, max_size=3))
def test_short_paths_consistency(path_str):
    """Test very short path strings for consistency."""
    try:
        path = PurePath(path_str)
        
        # Test that operations are consistent
        assert PurePath(str(path)) == path
        
        # Parent of a path should be idempotent at root
        parent1 = path.parent
        parent2 = parent1.parent
        
        # Eventually we should reach a fixed point
        iterations = 0
        current = path
        while current.parent != current and iterations < 100:
            current = current.parent
            iterations += 1
        assert iterations < 100  # Should not infinite loop
        
    except (ValueError, TypeError):
        pass  # Some inputs might not be valid paths


@given(st.text(alphabet=string.whitespace, min_size=1, max_size=10))
def test_whitespace_paths(whitespace):
    """Test paths consisting only of whitespace."""
    path = PurePath(whitespace)
    
    # Should handle whitespace without crashing
    assert isinstance(path, PurePath)
    
    # Converting to string and back should work
    path_str = str(path)
    path2 = PurePath(path_str)
    assert path == path2


@given(st.lists(st.sampled_from([".", ".."]), min_size=1, max_size=10))
def test_dot_components(components):
    """Test paths with only . and .. components."""
    path_str = "/".join(components)
    path = PurePath(path_str)
    
    # These should be valid paths
    assert isinstance(path, PurePath)
    
    # Converting to string should work
    str(path)
    
    # Parent operation should work
    _ = path.parent


@given(st.text(alphabet="/\\", min_size=1, max_size=20))
def test_mixed_separators(separators):
    """Test paths with mixed forward and back slashes."""
    # Add some components
    path_str = f"a{separators}b{separators}c"
    
    # PurePosixPath should handle forward slashes
    posix_path = PurePosixPath(path_str)
    assert isinstance(posix_path, PurePosixPath)
    
    # On Windows, PureWindowsPath should handle both
    if os.name == 'nt':
        win_path = PureWindowsPath(path_str)
        assert isinstance(win_path, PureWindowsPath)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
       st.integers(min_value=1, max_value=1000))
def test_deeply_nested_paths(component, depth):
    """Test very deeply nested paths."""
    # Create a path with many levels
    components = [component] * depth
    path = PurePath(*components)
    
    # Should handle deep nesting
    assert len(path.parts) == depth
    
    # Parent chain should work
    current = path
    for _ in range(min(10, depth)):
        current = current.parent
    
    # String representation should work
    path_str = str(path)
    assert component in path_str


@given(st.text(min_size=1, max_size=5).filter(lambda s: s and s not in [".", ".."]))
def test_with_name_edge_cases(name):
    """Test with_name with various inputs."""
    base = PurePath("dir/file.txt")
    
    try:
        new_path = base.with_name(name)
        assert new_path.name == name
        assert new_path.parent == base.parent
    except ValueError:
        # Some names might be invalid (e.g., containing /)
        assume("/" not in name and "\\" not in name)


@given(st.sampled_from(["", ".", "..", "/"]))
def test_with_name_invalid_inputs(invalid_name):
    """Test with_name with known invalid inputs."""
    base = PurePath("dir/file.txt")
    
    # These should raise ValueError
    with pytest.raises(ValueError):
        base.with_name(invalid_name)


@given(st.text(alphabet=string.ascii_letters + ".", min_size=1, max_size=20))
def test_suffixes_property(filename):
    """Test the suffixes property (returns list of all suffixes)."""
    assume("/" not in filename and "\\" not in filename)
    assume(filename not in [".", ".."])
    
    path = PurePath(filename)
    suffixes = path.suffixes
    
    # suffixes should be a list
    assert isinstance(suffixes, list)
    
    # All elements should start with .
    for suffix in suffixes:
        assert suffix.startswith(".")
    
    # The last suffix should match path.suffix (if any)
    if suffixes:
        assert suffixes[-1] == path.suffix
    elif path.suffix:
        assert False, f"path.suffix={path.suffix} but suffixes is empty"


@given(st.text(min_size=0, max_size=50))
def test_match_pattern(path_str):
    """Test the match method with patterns."""
    try:
        path = PurePath(path_str)
        
        # Should match itself
        if path_str:
            # match works with glob patterns
            assert path.match(path_str) or "/" in path_str or "\\" in path_str
            
        # Should match with *
        assert path.match("*") or "/" in str(path)
        
        # Should match with ** pattern
        pattern = "**/" + path.name if path.name else "**"
        try:
            path.match(pattern)
        except ValueError:
            pass  # Some patterns might be invalid
            
    except (ValueError, TypeError):
        pass


@given(st.lists(st.text(min_size=1, max_size=5), min_size=2, max_size=4))
def test_relative_to_with_walk_up(components):
    """Test relative_to with walk_up parameter (Python 3.12+)."""
    base = PurePath(*components[:-1])
    full = PurePath(*components)
    
    # full should be relative to base
    assert full.is_relative_to(base)
    
    # But base is not relative to full normally
    assert not base.is_relative_to(full)
    
    # With walk_up=True, we should be able to get from full to base
    try:
        # This feature was added in Python 3.12
        rel = base.relative_to(full, walk_up=True)
        # Should contain .. components
        assert ".." in rel.parts
    except TypeError:
        # Python < 3.12 doesn't support walk_up parameter
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])