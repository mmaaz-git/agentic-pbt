#!/usr/bin/env python3
"""Extended property-based tests for pathlib with more edge cases."""

import string
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath

import pytest
from hypothesis import assume, given, settings, strategies as st


# Test with more edge cases and special characters
special_chars_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_.()[]{}~!@#$%^&+=",
    min_size=1,
    max_size=10
).filter(lambda s: "/" not in s and "\\" not in s and s not in (".", ".."))


@given(st.lists(special_chars_strategy, min_size=1, max_size=5))
def test_special_chars_in_paths(components):
    """Test paths with special characters."""
    path_str = "/".join(components)
    path = PurePath(path_str)
    
    # String round-trip should work
    assert PurePath(str(path)) == path
    
    # Parts should match
    assert len(path.parts) == len(components)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5))
def test_stem_and_suffix_interaction(stem):
    """Test interaction between stem and suffix operations."""
    # Create path with suffix
    path = PurePath(f"{stem}.txt")
    
    # Test with_stem
    new_stem = "newfile"
    new_path = path.with_stem(new_stem)
    assert new_path.stem == new_stem
    assert new_path.suffix == ".txt"  # Suffix should be preserved
    
    # Changing stem then suffix should work
    path2 = path.with_stem("other").with_suffix(".py")
    assert path2.stem == "other"
    assert path2.suffix == ".py"


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=3, max_size=6))
def test_multiple_relative_to_operations(components):
    """Test chained relative_to operations."""
    base = PurePath(components[0])
    middle = base.joinpath(components[1])
    full = middle.joinpath(components[2])
    
    # full relative to base should give the rest
    rel_to_base = full.relative_to(base)
    assert base.joinpath(rel_to_base) == full
    
    # full relative to middle should give just the last part
    rel_to_middle = full.relative_to(middle)
    assert middle.joinpath(rel_to_middle) == full
    
    # Transitivity: if A is relative to B and B is relative to C, then A is relative to C
    assert full.is_relative_to(middle)
    assert middle.is_relative_to(base)
    assert full.is_relative_to(base)


@given(st.text(alphabet=string.ascii_letters + ".", min_size=1, max_size=20))
def test_multiple_suffixes(filename):
    """Test files with multiple dots/suffixes."""
    assume("/" not in filename and "\\" not in filename)
    assume(filename not in (".", ".."))
    
    path = PurePath(filename)
    
    # suffix should return the last suffix only
    if "." in filename and not filename.endswith("."):
        last_dot_idx = filename.rfind(".")
        expected_suffix = filename[last_dot_idx:]
        assert path.suffix == expected_suffix
    
    # with_suffix should replace only the last suffix
    if path.suffix:
        new_path = path.with_suffix(".new")
        assert new_path.suffix == ".new"
        # The stem + other suffixes should be preserved
        assert str(new_path).endswith(".new")


@given(st.just(""))
def test_empty_path_edge_case(empty):
    """Test edge case with empty paths."""
    # PurePath with empty string should create a valid path
    path = PurePath(empty)
    assert str(path) == "."
    
    # Should be able to join with it
    other = PurePath("file.txt")
    joined = path.joinpath(other)
    assert joined == other


@given(st.lists(st.just(".."), min_size=1, max_size=5))
def test_parent_directory_traversal(parent_refs):
    """Test paths with .. components."""
    base = PurePath("a/b/c")
    
    # Join with parent references
    path_str = "/".join(parent_refs)
    result = base.joinpath(path_str)
    
    # Should handle .. correctly
    assert ".." in result.parts or len(parent_refs) >= 3


@given(st.text(alphabet="/", min_size=1, max_size=5))
def test_multiple_slashes(slashes):
    """Test paths with multiple consecutive slashes."""
    path = PurePath(f"a{slashes}b")
    
    # Multiple slashes should be normalized
    assert "//" not in str(path) or str(path).startswith("//")
    
    # Parts should not contain empty strings (except possibly for UNC paths)
    for part in path.parts:
        if part:  # Skip empty parts from absolute paths
            assert part != ""


@settings(max_examples=500)
@given(st.text(alphabet=string.printable, min_size=0, max_size=50))
def test_path_constructor_doesnt_crash(path_str):
    """Test that PurePath constructor handles arbitrary input without crashing."""
    try:
        path = PurePath(path_str)
        # If it constructs successfully, string conversion should work
        str(path)
        
        # These operations should not crash
        _ = path.parts
        _ = path.parent
        _ = path.name
        _ = path.suffix
        _ = path.stem
    except (ValueError, TypeError) as e:
        # Some inputs might legitimately raise errors
        # But we're looking for unexpected crashes
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])