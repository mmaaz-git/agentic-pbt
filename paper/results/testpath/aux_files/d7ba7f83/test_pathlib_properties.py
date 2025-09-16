#!/usr/bin/env python3
"""Property-based tests for Python's pathlib module using Hypothesis."""

import os
import string
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath

import pytest
from hypothesis import assume, given, settings, strategies as st


# Custom strategies for generating valid path components
def path_component_strategy():
    """Generate valid path components (no slashes, not . or ..)"""
    return st.text(
        alphabet=string.ascii_letters + string.digits + "-_.",
        min_size=1,
        max_size=20
    ).filter(lambda s: s not in (".", "..", "") and "/" not in s and "\\" not in s)


def path_string_strategy():
    """Generate valid path strings."""
    components = st.lists(path_component_strategy(), min_size=1, max_size=5)
    return components.map(lambda parts: "/".join(parts))


def suffix_strategy():
    """Generate valid file suffixes."""
    return st.one_of(
        st.just(""),  # Empty suffix
        st.text(alphabet=string.ascii_lowercase + string.digits, min_size=1, max_size=5).map(lambda s: f".{s}")
    )


@given(path_string_strategy())
def test_path_string_roundtrip(path_str):
    """Test that Path(str(path)) == path for PurePath objects."""
    path = PurePath(path_str)
    reconstructed = PurePath(str(path))
    assert reconstructed == path
    assert str(reconstructed) == str(path)


@given(path_string_strategy(), path_string_strategy())
def test_joinpath_relative_to_inverse(base_str, extension_str):
    """Test that joinpath and relative_to are inverse operations when applicable."""
    base = PurePath(base_str)
    full_path = base.joinpath(extension_str)
    
    # full_path should be relative to base
    assert full_path.is_relative_to(base)
    
    # Getting the relative part and joining it back should give the original
    relative_part = full_path.relative_to(base)
    reconstructed = base.joinpath(relative_part)
    assert reconstructed == full_path


@given(path_string_strategy(), path_string_strategy())
def test_is_relative_to_implies_relative_to_works(path1_str, path2_str):
    """Test that if is_relative_to returns True, relative_to doesn't raise."""
    path1 = PurePath(path1_str)
    path2 = PurePath(path2_str)
    
    if path1.is_relative_to(path2):
        # This should not raise ValueError
        try:
            relative = path1.relative_to(path2)
            # The relative path joined with path2 should give back path1
            assert path2.joinpath(relative) == path1
        except ValueError as e:
            pytest.fail(f"relative_to raised ValueError despite is_relative_to being True: {e}")


@given(path_string_strategy(), suffix_strategy())
def test_with_suffix_sets_correct_suffix(path_str, suffix):
    """Test that with_suffix correctly sets the suffix."""
    path = PurePath(path_str)
    
    # Skip if path ends with a slash (directory paths)
    assume(not path_str.endswith("/"))
    
    new_path = path.with_suffix(suffix)
    
    if suffix == "":
        # Empty suffix should remove the suffix
        assert new_path.suffix == ""
    else:
        # Non-empty suffix should be set correctly
        assert new_path.suffix == suffix


@given(path_string_strategy())
def test_parent_parts_invariant(path_str):
    """Test that a path has at least as many parts as its parent."""
    path = PurePath(path_str)
    
    # Skip the root path case
    if path.parent != path:
        assert len(path.parts) > len(path.parent.parts)
        # Parent should have exactly one less part (except for edge cases)
        assert path.parts[:-1] == path.parent.parts


@given(st.lists(path_component_strategy(), min_size=2, max_size=5))
def test_joinpath_associativity(components):
    """Test that joinpath is associative: p.joinpath(a, b) == p.joinpath(a).joinpath(b)"""
    if len(components) < 3:
        return
    
    base = PurePath(components[0])
    rest = components[1:]
    
    # Join all at once
    all_at_once = base.joinpath(*rest)
    
    # Join one by one
    one_by_one = base
    for component in rest:
        one_by_one = one_by_one.joinpath(component)
    
    assert all_at_once == one_by_one


@given(path_string_strategy())
def test_as_posix_uses_forward_slashes(path_str):
    """Test that as_posix() always uses forward slashes."""
    path = PurePath(path_str)
    posix_str = path.as_posix()
    
    # Should not contain backslashes
    assert "\\" not in posix_str
    # Should preserve the path structure
    assert "/" in posix_str or len(path.parts) == 1


@given(path_string_strategy(), suffix_strategy(), suffix_strategy())
def test_suffix_replacement_consistency(path_str, suffix1, suffix2):
    """Test that replacing suffixes is consistent."""
    path = PurePath(path_str)
    
    # Skip if path ends with a slash
    assume(not path_str.endswith("/"))
    
    # Apply suffix1, then suffix2
    path_with_suffix1 = path.with_suffix(suffix1)
    path_with_suffix2 = path_with_suffix1.with_suffix(suffix2)
    
    # Should be the same as applying suffix2 directly to the original
    path_direct = path.with_suffix(suffix2)
    
    assert path_with_suffix2 == path_direct


@given(path_string_strategy())
def test_parts_join_reconstruction(path_str):
    """Test that joining parts reconstructs the path."""
    path = PurePath(path_str)
    
    if len(path.parts) > 0:
        # Reconstruct from parts
        if len(path.parts) == 1:
            reconstructed = PurePath(path.parts[0])
        else:
            reconstructed = PurePath(path.parts[0]).joinpath(*path.parts[1:])
        
        # Should be equivalent
        assert reconstructed == path


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])