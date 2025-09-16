"""Focused tests on specific corner cases that might reveal bugs"""

import os
import os.path
import sys
from hypothesis import given, strategies as st, assume, settings, example
import string


def test_commonpath_with_mixed_separators():
    """Test commonpath with paths that might have inconsistent separators"""
    test_cases = [
        (["/foo/bar", "/foo\\baz"], "commonpath with backslash"),
        (["/foo//bar", "/foo/baz"], "commonpath with double slash"),
        (["/foo/./bar", "/foo/baz"], "commonpath with dot component"),
        (["/foo", "/foo/"], "one path with trailing slash"),
    ]
    
    for paths, description in test_cases:
        print(f"  Testing {description}: {paths}")
        try:
            result = os.path.commonpath(paths)
            print(f"    Result: {repr(result)}")
            
            # Verify the result is actually a common prefix
            for p in paths:
                norm_p = os.path.normpath(p)
                norm_result = os.path.normpath(result)
                if not norm_p.startswith(norm_result):
                    print(f"    ❌ POTENTIAL BUG: {repr(p)} doesn't start with {repr(result)}")
                    return False
        except Exception as e:
            print(f"    Exception: {e}")
    
    return True


def test_join_empty_string_behavior():
    """Test how join handles empty strings"""
    test_cases = [
        (["", "foo"], "empty first component"),
        (["foo", ""], "empty second component"),
        (["", ""], "both empty"),
        (["foo", "", "bar"], "empty middle component"),
        (["", "foo", ""], "empty first and last"),
    ]
    
    for components, description in test_cases:
        print(f"  Testing {description}: {components}")
        result = os.path.join(*components)
        print(f"    Result: {repr(result)}")
        
        # Check specific expectations
        if components == ["", ""]:
            if result != "":
                print(f"    ❌ POTENTIAL BUG: join('', '') = {repr(result)}, expected ''")
                return False
    
    return True


def test_splitdrive_behavior():
    """Test splitdrive on various inputs"""
    @given(st.text(min_size=0, max_size=100).filter(lambda x: '\x00' not in x))
    def check_splitdrive(path):
        drive, tail = os.path.splitdrive(path)
        rejoined = drive + tail
        assert rejoined == path, f"splitdrive round-trip failed: {repr(path)} != {repr(rejoined)}"
        
        # On Unix, drive should usually be empty
        if sys.platform not in ('win32', 'cygwin'):
            if drive and not path.startswith("//"):
                print(f"Unexpected drive on Unix: {repr(drive)} for path {repr(path)}")
    
    check_splitdrive()


def test_normpath_special_cases():
    """Test normpath with very specific edge cases"""
    special_cases = [
        "",  # empty string
        "//",  # double slash (UNC on Windows, special on Unix)
        "///",  # triple slash
        "//foo",  # UNC-like path
        "/..",  # trying to go above root
        "/../..",  # multiple levels above root
        "/./././",  # multiple current dir refs
        "foo/",  # trailing slash
        "./",  # current dir with slash
        "../",  # parent dir with slash
    ]
    
    for path in special_cases:
        norm = os.path.normpath(path)
        norm2 = os.path.normpath(norm)
        print(f"  {repr(path):20} -> {repr(norm):20} (idempotent: {norm == norm2})")
        
        if norm != norm2:
            print(f"    ❌ POTENTIAL BUG: normpath not idempotent!")
            return False
    
    return True


def test_realpath_symlink_behavior():
    """Test realpath behavior (without actual symlinks, just the function behavior)"""
    @given(st.text(min_size=0, max_size=50).filter(lambda x: '\x00' not in x))
    @settings(max_examples=100)
    def check_realpath(path):
        try:
            # realpath should be idempotent
            real1 = os.path.realpath(path)
            real2 = os.path.realpath(real1)
            assert real1 == real2, f"realpath not idempotent: {repr(path)} -> {repr(real1)} -> {repr(real2)}"
            
            # realpath result should be absolute
            assert os.path.isabs(real1), f"realpath didn't return absolute path: {repr(real1)}"
            
        except (OSError, ValueError):
            # Some paths might fail
            pass
    
    check_realpath()


def test_expandvars_edge_cases():
    """Test expandvars with various variable patterns"""
    test_cases = [
        ("$", "lone dollar sign"),
        ("$$", "double dollar"),
        ("${}", "empty braces"),
        ("${", "unclosed brace"),
        ("$123", "numeric after dollar"),
        ("$-test", "dash after dollar"),
        ("${VAR", "unclosed bracket"),
        ("$VAR$VAR", "multiple vars"),
        ("${VAR:-default}", "bash-style default"),
    ]
    
    for path, description in test_cases:
        print(f"  Testing {description}: {repr(path)}")
        try:
            result = os.path.expandvars(path)
            print(f"    Result: {repr(result)}")
            
            # expandvars should be idempotent if no vars were expanded
            result2 = os.path.expandvars(result)
            if '$' not in result and result != result2:
                print(f"    ❌ POTENTIAL BUG: expandvars not idempotent when no $ in result")
                return False
                
        except Exception as e:
            print(f"    Exception: {e}")
            return False
    
    return True


def test_path_component_extraction():
    """Test that we can correctly extract and reconstruct paths"""
    @given(st.text(min_size=1, max_size=100).filter(lambda x: '\x00' not in x))
    @settings(max_examples=200)
    def check_extraction(path):
        # Skip Windows drive paths on Unix
        if sys.platform not in ('win32', 'cygwin') and ':' in path[:3]:
            return
            
        # Extract all components
        drive, path_no_drive = os.path.splitdrive(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        root, ext = os.path.splitext(path)
        
        # Some consistency checks
        if basename:
            # If there's a basename, dirname + basename should reconstruct something equivalent
            reconstructed = os.path.join(dirname, basename)
            # Normalize both for comparison
            assert os.path.normpath(reconstructed) == os.path.normpath(path), \
                f"dirname+basename reconstruction failed: {repr(path)} != {repr(reconstructed)}"
    
    check_extraction()


if __name__ == "__main__":
    print("Testing os module corner cases...")
    
    print("\n1. Testing commonpath with mixed separators...")
    if test_commonpath_with_mixed_separators():
        print("   ✓ Passed")
    else:
        print("   ⚠ Potential issue found")
    
    print("\n2. Testing join with empty strings...")
    if test_join_empty_string_behavior():
        print("   ✓ Passed")
    else:
        print("   ⚠ Potential issue found")
    
    print("\n3. Testing splitdrive behavior...")
    test_splitdrive_behavior()
    print("   ✓ Passed")
    
    print("\n4. Testing normpath special cases...")
    if test_normpath_special_cases():
        print("   ✓ Passed")
    else:
        print("   ⚠ Potential issue found")
    
    print("\n5. Testing realpath behavior...")
    test_realpath_symlink_behavior()
    print("   ✓ Passed")
    
    print("\n6. Testing expandvars edge cases...")
    if test_expandvars_edge_cases():
        print("   ✓ Passed")
    else:
        print("   ⚠ Potential issue found")
    
    print("\n7. Testing path component extraction...")
    test_path_component_extraction()
    print("   ✓ Passed")
    
    print("\nCorner case testing complete!")