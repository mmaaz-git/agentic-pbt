import pathlib
import os
from hypothesis import given, strategies as st, assume, settings
import string
import math

# Strategy for valid path component names (no path separators)
path_component = st.text(
    alphabet=string.ascii_letters + string.digits + "._-",
    min_size=1,
    max_size=20
).filter(lambda s: s not in (".", "..") and "/" not in s and "\\" not in s)

# Strategy for file extensions
extension = st.text(
    alphabet=string.ascii_lowercase + string.digits,
    min_size=1, 
    max_size=5
).map(lambda s: f".{s}")

# Strategy for path strings
def path_string_strategy():
    return st.one_of(
        # Simple filename
        path_component,
        # Filename with extension
        st.builds(lambda n, e: n + e, path_component, extension),
        # Path with directory
        st.builds(lambda d, f: f"{d}/{f}", path_component, path_component),
        # Path with multiple extensions
        st.builds(lambda n, e1, e2: n + e1 + e2, path_component, extension, extension),
    )

@given(path_string_strategy())
def test_name_stem_suffix_relationship(path_str):
    """Test: name = stem + suffix (for paths with names)"""
    p = pathlib.PurePath(path_str)
    if p.name:  # Only test when there's a name
        reconstructed = p.stem + p.suffix
        assert p.name == reconstructed, f"name={p.name!r} != stem+suffix={reconstructed!r}"

@given(path_string_strategy())  
def test_suffix_in_suffixes(path_str):
    """Test: suffix should be the last element in suffixes (when present)"""
    p = pathlib.PurePath(path_str)
    if p.suffix:
        assert p.suffixes, f"suffix={p.suffix!r} but suffixes is empty"
        assert p.suffixes[-1] == p.suffix, f"suffix={p.suffix!r} != suffixes[-1]={p.suffixes[-1]!r}"

@given(path_string_strategy())
def test_joinpath_parts_relationship(path_str):
    """Test: joining parts should reconstruct the path"""
    p = pathlib.PurePath(path_str)
    if p.parts:
        reconstructed = pathlib.PurePath(*p.parts)
        assert str(reconstructed) == str(p), f"PurePath(*parts) != original: {reconstructed} != {p}"

@given(path_component, extension)
def test_with_suffix_roundtrip(name, ext):
    """Test: p.with_suffix(ext).suffix == ext"""
    p = pathlib.PurePath(name)
    p_with_ext = p.with_suffix(ext)
    assert p_with_ext.suffix == ext, f"with_suffix({ext!r}).suffix = {p_with_ext.suffix!r}"

@given(path_component, path_component)
def test_with_name_changes_name(old_name, new_name):
    """Test: p.with_name(new).name == new"""
    p = pathlib.PurePath(f"dir/{old_name}")
    p_new = p.with_name(new_name)
    assert p_new.name == new_name, f"with_name({new_name!r}).name = {p_new.name!r}"

@given(path_component, path_component)
def test_with_stem_changes_stem(name, new_stem):
    """Test: p.with_stem(new).stem == new"""
    p = pathlib.PurePath(name + ".txt")
    p_new = p.with_stem(new_stem)
    assert p_new.stem == new_stem, f"with_stem({new_stem!r}).stem = {p_new.stem!r}"
    # Also check suffix is preserved
    assert p_new.suffix == ".txt", f"suffix changed from .txt to {p_new.suffix!r}"

@given(st.lists(path_component, min_size=1, max_size=5))
def test_joinpath_associativity(components):
    """Test: (a / b) / c == a / (b / c)"""
    if len(components) >= 3:
        a, b, c = components[0], components[1], "/".join(components[2:])
        p1 = pathlib.PurePath(a).joinpath(b).joinpath(c)
        p2 = pathlib.PurePath(a).joinpath(pathlib.PurePath(b).joinpath(c))
        assert str(p1) == str(p2), f"joinpath not associative: {p1} != {p2}"

@given(path_string_strategy())
def test_parent_child_relationship(path_str):
    """Test: parent of a path should be shorter or equal in parts"""
    p = pathlib.PurePath(path_str)
    parent = p.parent
    # Parent should have fewer or equal parts (equal when path is root or current dir)
    assert len(parent.parts) <= len(p.parts), f"parent has more parts: {parent.parts} > {p.parts}"

@given(path_string_strategy())
def test_as_posix_idempotent(path_str):
    """Test: as_posix() should be idempotent"""
    p = pathlib.PurePath(path_str)
    posix1 = p.as_posix()
    p2 = pathlib.PurePath(posix1)
    posix2 = p2.as_posix()
    assert posix1 == posix2, f"as_posix not idempotent: {posix1!r} != {posix2!r}"

@given(st.lists(path_component, min_size=2, max_size=5))
def test_relative_to_basic(components):
    """Test: path.relative_to(parent) should work for actual subpaths"""
    # Build nested path
    full_path = pathlib.PurePath(*components)
    parent_path = pathlib.PurePath(*components[:-1])
    
    # Get relative path
    rel = full_path.relative_to(parent_path)
    
    # Joining parent with relative should give back full path
    reconstructed = parent_path / rel
    assert str(reconstructed) == str(full_path), f"relative_to broken: {parent_path} / {rel} != {full_path}"

@given(path_string_strategy(), st.text(min_size=0, max_size=3))
def test_match_glob_suffix(path_str, ext):
    """Test: paths ending with X should match pattern *X"""
    p = pathlib.PurePath(path_str)
    if ext and str(p).endswith(ext):
        pattern = f"*{ext}"
        assert p.match(pattern), f"{p} should match pattern {pattern!r}"

@given(path_component)
def test_with_suffix_empty_removes_suffix(name):
    """Test: with_suffix('') should remove the suffix"""
    p = pathlib.PurePath(name + ".txt")
    p_no_suffix = p.with_suffix('')
    assert p_no_suffix.suffix == '', f"with_suffix('') didn't remove suffix: {p_no_suffix.suffix!r}"
    assert p_no_suffix.stem == p.stem, f"stem changed: {p_no_suffix.stem!r} != {p.stem!r}"

@given(st.lists(extension, min_size=1, max_size=3))
def test_suffixes_consistency(extensions):
    """Test: all suffixes should start with a dot"""
    name = "file" + "".join(extensions)
    p = pathlib.PurePath(name)
    for suffix in p.suffixes:
        assert suffix.startswith('.'), f"Suffix doesn't start with dot: {suffix!r}"

@given(path_string_strategy())
def test_truediv_operator_consistency(path_str):
    """Test: p / 'x' should equal p.joinpath('x')"""
    p = pathlib.PurePath(path_str)
    component = "test"
    
    joined = p.joinpath(component)
    divided = p / component
    
    assert str(joined) == str(divided), f"joinpath != /: {joined} != {divided}"

# Test with more complex paths including special cases
special_paths = st.sampled_from([
    "",
    ".",
    "..",
    "/",
    "//",
    "///multiple/slashes//",
    ".hidden",
    "..double",
    "file.",
    "file..",
    "file...",
])

@given(special_paths)
def test_special_paths_dont_crash(path_str):
    """Test: special path strings should not cause crashes"""
    try:
        p = pathlib.PurePath(path_str)
        # Try various operations that might fail
        _ = p.name
        _ = p.stem
        _ = p.suffix
        _ = p.parts
        _ = p.parent
        _ = p.as_posix()
    except (ValueError, TypeError) as e:
        # These exceptions are acceptable for invalid paths
        pass

@given(path_component)
def test_with_name_preserves_parent(name):
    """Test: with_name should preserve the parent directory"""
    p = pathlib.PurePath(f"parent/child/{name}")
    p_new = p.with_name("newname")
    assert p.parent == p_new.parent, f"Parent changed: {p.parent} != {p_new.parent}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])