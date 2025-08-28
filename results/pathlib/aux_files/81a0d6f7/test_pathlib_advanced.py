import pathlib
import sys
from hypothesis import given, strategies as st, assume, settings
import os

# Test for edge cases and special characters
special_chars = st.text(alphabet="\x00\n\r\t ", min_size=1, max_size=5)

@given(st.text(min_size=1))
def test_match_case_sensitivity(pattern):
    """Test that match respects case_sensitive parameter"""
    # Create paths with different cases
    lower_path = pathlib.PurePath("test/file.txt")
    upper_path = pathlib.PurePath("TEST/FILE.TXT")
    
    # Skip if pattern would cause issues
    assume(pattern and "*" not in pattern and "?" not in pattern)
    
    try:
        # Test with case_sensitive=False (if supported)
        lower_match_insensitive = lower_path.match(pattern, case_sensitive=False)
        upper_match_insensitive = upper_path.match(pattern, case_sensitive=False)
        
        # Test with case_sensitive=True
        lower_match_sensitive = lower_path.match(pattern, case_sensitive=True)
        upper_match_sensitive = upper_path.match(pattern, case_sensitive=True)
        
        # If pattern matches one case-insensitively, it should match both
        if pattern.lower() in str(lower_path).lower():
            if lower_match_insensitive != upper_match_insensitive:
                print(f"Case sensitivity issue: {pattern}")
    except (ValueError, TypeError):
        pass

@given(st.lists(st.text(alphabet="/", min_size=1), min_size=1, max_size=10))
def test_multiple_slashes(components):
    """Test paths with multiple consecutive slashes"""
    # Join with multiple slashes
    path_str = "//".join(components)
    
    try:
        p = pathlib.PurePath(path_str)
        # Multiple slashes should be normalized
        assert "//" not in p.as_posix() or p.as_posix().startswith("//"), \
            f"Multiple slashes not normalized: {path_str} -> {p.as_posix()}"
    except (ValueError, OSError):
        pass

@given(st.text())
def test_relative_to_with_dots(path_str):
    """Test relative_to with paths containing . and .."""
    assume(path_str and path_str not in (".", ".."))
    
    try:
        base = pathlib.PurePath("a/b/c")
        target = base / path_str
        
        # Try to get relative path
        if ".." not in path_str:
            rel = target.relative_to(base)
            reconstructed = base / rel
            assert str(reconstructed) == str(target), \
                f"relative_to failed: {base} / {rel} != {target}"
    except (ValueError, TypeError):
        pass

@given(st.text(min_size=1).filter(lambda x: "\x00" not in x and "/" not in x))
def test_is_reserved_windows_names(name):
    """Test Windows reserved name detection"""
    p = pathlib.PureWindowsPath(name)
    
    # Known Windows reserved names
    reserved = {"CON", "PRN", "AUX", "NUL", 
                "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    
    base_name = name.upper().split(".")[0] if "." in name else name.upper()
    
    if base_name in reserved:
        assert p.is_reserved(), f"{name} should be reserved but isn't"

@given(st.lists(st.text(min_size=1).filter(lambda x: "/" not in x and "\\" not in x), 
                min_size=2, max_size=5))
def test_parents_iteration(components):
    """Test that parents iteration works correctly"""
    p = pathlib.PurePath(*components)
    
    parents_list = list(p.parents)
    
    # Each parent should be the parent of the previous
    for i in range(len(parents_list) - 1):
        assert parents_list[i].parent == parents_list[i + 1], \
            f"Parents chain broken at {i}: {parents_list[i].parent} != {parents_list[i + 1]}"
    
    # Last parent should be root or current dir
    if parents_list:
        last = parents_list[-1]
        assert str(last) in (".", "/"), f"Last parent is not root: {last}"

@given(st.text(min_size=1))
def test_full_match_vs_match(path_str):
    """Test difference between match and full_match"""
    assume(path_str and "*" not in path_str and "?" not in path_str)
    
    p = pathlib.PurePath("dir/subdir/file.txt")
    
    try:
        # full_match should match from the beginning
        # match can match from any parent
        match_result = p.match(path_str)
        full_match_result = p.full_match(path_str)
        
        # If full_match succeeds, match should also succeed
        if full_match_result:
            assert match_result, f"full_match succeeded but match failed for {path_str}"
    except (ValueError, TypeError):
        pass

@given(st.text())
def test_with_segments_edge_cases(segment):
    """Test with_segments with various inputs"""
    p = pathlib.PurePath("original/path")
    
    try:
        # with_segments should replace the entire path
        new_p = p.with_segments(segment)
        
        if segment:
            assert str(new_p) == segment or str(new_p) == segment.replace("//", "/"), \
                f"with_segments didn't replace path: {new_p} != {segment}"
        else:
            # Empty segment might be special
            assert str(new_p) == "." or str(new_p) == "", \
                f"with_segments('') gave unexpected result: {new_p}"
    except (ValueError, TypeError, AttributeError):
        # with_segments might not exist in older versions
        pass

@given(st.lists(st.sampled_from([".", "..", "/"]), min_size=1, max_size=10))  
def test_special_components_normalization(components):
    """Test normalization of special path components"""
    path_str = "/".join(components)
    
    try:
        p = pathlib.PurePath(path_str)
        
        # Path should be normalized
        posix = p.as_posix()
        
        # Should not have //. or /./ patterns (except at start)
        assert "//." not in posix[2:], f"Invalid pattern //. in {posix}"
        assert "/./" not in posix[2:], f"Invalid pattern /./ in {posix}"
        
    except (ValueError, OSError):
        pass

# Test symlink and junction related edge cases
@given(st.text(min_size=1).filter(lambda x: "/" not in x and "\\" not in x))
def test_stat_vs_lstat_difference(filename):
    """Test that stat and lstat would differ for symlinks"""
    # This test would need actual filesystem access
    # Checking the methods exist and have different implementations
    
    # Create a path
    p = pathlib.Path(filename)
    
    # These methods should exist
    assert hasattr(p, 'stat'), "stat method missing"
    assert hasattr(p, 'lstat'), "lstat method missing"
    
    # They should be different methods
    assert p.stat != p.lstat, "stat and lstat are the same method"

if __name__ == "__main__":
    import pytest
    # Run with limited examples for speed
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])