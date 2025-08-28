import pathlib
from hypothesis import given, strategies as st, assume, settings, example
import sys
import os

# Test for potential bugs in path resolution and manipulation

@given(st.text(min_size=1))
def test_as_uri_special_chars(path_str):
    """Test as_uri with special characters"""
    # Focus on absolute paths for URI
    assume(path_str and "\x00" not in path_str)
    
    try:
        # Make it absolute for URI conversion
        p = pathlib.PurePath("/test" / path_str)
        
        if p.is_absolute():
            uri = p.as_uri()
            
            # URI should start with file://
            assert uri.startswith("file://"), f"URI doesn't start with file://: {uri}"
            
            # Special characters should be encoded
            if " " in str(p):
                assert "%20" in uri or " " not in uri, f"Spaces not encoded in URI: {uri}"
                
    except (ValueError, TypeError, NotImplementedError):
        pass

@given(st.text())
@example("")  # Empty string edge case
@example(".")
@example("..")  
@example("//")
def test_with_name_empty_edge_cases(new_name):
    """Test with_name with edge case inputs"""
    p = pathlib.PurePath("/dir/file.txt")
    
    try:
        result = p.with_name(new_name)
        
        # The new name should be what we set (unless it's invalid)
        if new_name and "/" not in new_name:
            assert result.name == new_name, f"with_name failed: {result.name} != {new_name}"
            
    except ValueError as e:
        # Some names should raise ValueError
        if new_name in ("", ".", "..") or "/" in new_name or "\x00" in new_name:
            pass  # Expected to fail
        else:
            raise  # Unexpected failure

@given(st.text())
def test_joinpath_with_absolute_paths(path2):
    """Test joinpath behavior when second path is absolute"""
    p1 = pathlib.PurePath("/first/path")
    
    try:
        result = p1.joinpath(path2)
        
        # If path2 is absolute, it should replace p1
        if path2.startswith("/"):
            # Result should be based on path2, not p1
            assert not str(result).startswith("/first/path"), \
                f"Absolute path didn't replace: {p1} / {path2} = {result}"
                
    except (ValueError, TypeError):
        pass

@given(st.lists(st.text(min_size=1).filter(lambda x: "/" not in x), min_size=1))
def test_resolve_dots_in_path(components):
    """Test handling of . and .. in paths"""
    # Insert some dots
    with_dots = []
    for comp in components:
        with_dots.append(comp)
        with_dots.append(".")
        with_dots.append("..")
    
    try:
        p = pathlib.PurePath(*with_dots)
        
        # Count net directory depth
        depth = 0
        for part in p.parts:
            if part == "..":
                depth -= 1
            elif part != ".":
                depth += 1
                
        # Depth should be non-negative for valid paths
        if str(p)[0] != "/":  # Relative paths
            assert depth >= 0 or ".." in p.parts, \
                f"Invalid path normalization: {p} has depth {depth}"
                
    except (ValueError, IndexError):
        pass

@given(st.text(min_size=1, max_size=10))
def test_suffix_with_no_name(suffix):
    """Test suffix behavior on paths with no name"""
    # Paths with no name (like "/" or "dir/")
    
    for path_str in ["/", "dir/", "."]:
        p = pathlib.PurePath(path_str)
        
        if not p.name:
            # Can't have a suffix without a name
            assert p.suffix == "", f"Path {p} with no name has suffix {p.suffix}"
            
            # with_suffix should fail or do nothing
            try:
                result = p.with_suffix(suffix)
                # If it succeeds, it should be unchanged or have the suffix as name
                assert result == p or result.name == suffix.lstrip("."), \
                    f"Unexpected with_suffix on {p}: {result}"
            except ValueError:
                pass  # Expected for paths with no name

@given(st.integers(min_value=0, max_value=1000))
def test_parents_index_bounds(index):
    """Test parents indexing with various indices"""
    p = pathlib.PurePath("/a/b/c/d/e")
    
    try:
        parent = p.parents[index]
        
        # Should get progressively shorter paths
        if index == 0:
            assert parent == p.parent
        
        # Check we can also access via iteration
        parents_list = list(p.parents)
        if index < len(parents_list):
            assert parent == parents_list[index], \
                f"Parents index mismatch: parents[{index}] != list(parents)[{index}]"
                
    except IndexError:
        # Should only happen for out of bounds
        parents_list = list(p.parents)
        assert index >= len(parents_list), \
            f"Unexpected IndexError for index {index} (len={len(parents_list)})"

@given(st.sampled_from(["", ".", "..", "...", ".file", "..file"]))
def test_stem_of_dotfiles(name):
    """Test stem behavior with dot-prefixed files"""
    p = pathlib.PurePath(name)
    
    # Stem rules for special cases
    if name in (".", ".."):
        # These are special directories, not files with extensions
        assert p.stem == name, f"Special dir {name} has wrong stem: {p.stem}"
        assert p.suffix == "", f"Special dir {name} has suffix: {p.suffix}"
    elif name.startswith(".") and "." not in name[1:]:
        # Hidden files without extension (like .bashrc)
        assert p.stem == name, f"Hidden file {name} has wrong stem: {p.stem}"
        assert p.suffix == "", f"Hidden file {name} has unexpected suffix: {p.suffix}"

@given(st.text(alphabet="abc/", min_size=1, max_size=20))
def test_slash_combinations(path_str):
    """Test various slash combinations"""
    try:
        p = pathlib.PurePath(path_str)
        
        # as_posix should normalize slashes
        posix = p.as_posix()
        
        # Should not have empty components except at boundaries
        parts = p.parts
        for part in parts:
            if part not in ("/", ""):
                assert part, f"Empty part in {parts} from {path_str}"
                
        # No more than 2 leading slashes should be preserved
        if posix.startswith("///"):
            assert False, f"Too many leading slashes preserved: {posix}"
            
    except (ValueError, OSError):
        pass

@given(st.text(min_size=1))
def test_match_with_absolute_patterns(pattern):
    """Test match behavior with absolute path patterns"""
    assume(pattern)
    
    abs_path = pathlib.PurePath("/root/dir/file.txt")
    rel_path = pathlib.PurePath("dir/file.txt")
    
    try:
        # If pattern is absolute, behavior might differ
        if pattern.startswith("/"):
            abs_match = abs_path.match(pattern)
            rel_match = rel_path.match(pattern)
            
            # Relative path shouldn't match absolute pattern
            if rel_match and "/" in pattern:
                # Check if this makes sense
                pass
                
    except (ValueError, TypeError):
        pass

@given(st.text())
def test_relative_to_identity(path_str):
    """Test that path.relative_to(path) returns current dir"""
    assume(path_str and path_str != ".")
    
    try:
        p = pathlib.PurePath(path_str)
        
        # Path relative to itself should be current dir
        rel = p.relative_to(p)
        assert str(rel) == ".", f"Path relative to itself is not '.': {rel}"
        
    except ValueError:
        # Can happen for invalid paths
        pass

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])