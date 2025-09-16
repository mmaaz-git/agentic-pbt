"""More aggressive property-based tests for Python os module edge cases"""

import os
import os.path
import sys
from hypothesis import given, strategies as st, assume, settings, example
import tempfile
import uuid


# More aggressive path strategies
edge_paths = st.one_of(
    st.just(""),  # empty path
    st.just("."),  # current dir
    st.just(".."),  # parent dir  
    st.just("/"),  # root
    st.just("//"),  # double slash root
    st.just("///"),  # triple slash
    st.text(alphabet="/", min_size=1, max_size=100),  # only slashes
    st.text(alphabet="./", min_size=1, max_size=100),  # dots and slashes
    st.text().map(lambda x: f"/{x}/" if x else "/"),  # paths with trailing slash
    st.text().filter(lambda x: '\x00' not in x),  # random text
)

# Unicode-heavy paths
unicode_paths = st.text(
    alphabet=st.characters(min_codepoint=128, blacklist_categories=("Cs", "Cc")),
    min_size=0,
    max_size=50
).filter(lambda x: '\x00' not in x)


def test_splitext_with_multiple_dots():
    """Test splitext behavior with files having multiple dots"""
    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz.", min_size=1, max_size=50))
    @example("file.tar.gz")
    @example("......")
    @example("file...")
    @example(".hidden.txt")
    @example(".")
    @example("..")
    def check_multiple_dots(filename):
        root, ext = os.path.splitext(filename)
        rejoined = root + ext
        assert rejoined == filename, f"splitext round-trip failed for {repr(filename)}"
        
        # The extension should start with a dot if non-empty
        if ext:
            assert ext[0] == ".", f"Extension doesn't start with dot: {repr(ext)} from {repr(filename)}"
    
    check_multiple_dots()


def test_normpath_with_edge_cases():
    """Test normpath with tricky edge cases"""
    @given(edge_paths)
    @example("/../../../")
    @example("/foo/..")
    @example("foo/../../bar")
    @example("./././.")
    @settings(max_examples=500)
    def check_normpath_edges(path):
        norm1 = os.path.normpath(path)
        norm2 = os.path.normpath(norm1)
        assert norm1 == norm2, f"normpath not idempotent for edge case: {repr(path)}"
    
    check_normpath_edges()


def test_join_with_absolute_paths():
    """Test os.path.join behavior when mixing absolute and relative paths"""
    @given(st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x),
           st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x))
    def check_join_absolute(path1, path2):
        # When second path is absolute, join should return the second path
        abs_path2 = "/" + path2.lstrip("/")
        result = os.path.join(path1, abs_path2)
        
        # According to documentation, an absolute path component discards all previous components
        assert result == abs_path2, f"join({repr(path1)}, {repr(abs_path2)}) should return {repr(abs_path2)}, got {repr(result)}"
    
    check_join_absolute()


def test_commonpath_with_unicode():
    """Test commonpath with unicode paths"""
    @given(st.lists(
        st.tuples(
            st.just("/base"),
            unicode_paths
        ),
        min_size=2,
        max_size=5
    ))
    def check_unicode_commonpath(path_tuples):
        paths = []
        for base, suffix in path_tuples:
            # Clean up the suffix to avoid path traversal issues
            clean_suffix = suffix.replace("/", "_").replace("\x00", "")
            if clean_suffix:
                paths.append(base + "/" + clean_suffix)
        
        if len(paths) < 2:
            return
            
        try:
            common = os.path.commonpath(paths)
            # All paths should have the common path as prefix
            for p in paths:
                norm_p = os.path.normpath(p)
                norm_common = os.path.normpath(common)
                assert norm_p.startswith(norm_common), f"Path {repr(p)} doesn't start with common {repr(common)}"
        except (ValueError, TypeError) as e:
            # Some unicode might cause issues - that's a potential bug
            pass
    
    check_unicode_commonpath()


def test_split_with_only_separators():
    """Test split behavior with paths that are only separators"""
    @given(st.text(alphabet="/", min_size=1, max_size=100))
    def check_separator_only_paths(path):
        head, tail = os.path.split(path)
        # Properties should still hold
        assert head == os.path.dirname(path)
        assert tail == os.path.basename(path)
        
        # Rejoin if tail is not empty
        if tail:
            rejoined = os.path.join(head, tail)
            # Should preserve the path structure
            assert os.path.normpath(rejoined) == os.path.normpath(path)
    
    check_separator_only_paths()


def test_expanduser_consistency():
    """Test that expanduser is idempotent for already expanded paths"""
    @given(st.text(min_size=0, max_size=100).filter(lambda x: '\x00' not in x and not x.startswith('~')))
    def check_expanduser(path):
        # For paths not starting with ~, expanduser should return them unchanged
        expanded = os.path.expanduser(path)
        assert expanded == path, f"expanduser changed non-tilde path: {repr(path)} -> {repr(expanded)}"
        
        # Idempotence: expanding an already expanded path should not change it
        expanded2 = os.path.expanduser(expanded)
        assert expanded == expanded2, f"expanduser not idempotent: {repr(expanded)} -> {repr(expanded2)}"
    
    check_expanduser()


def test_relpath_with_same_path():
    """Test that relpath from a path to itself returns current directory marker"""
    @given(st.text(min_size=1, max_size=50).filter(lambda x: '\x00' not in x and x != ''))
    def check_relpath_same(path):
        try:
            # Get absolute path to avoid issues
            abs_path = os.path.abspath(path)
            rel = os.path.relpath(abs_path, abs_path)
            
            # Path relative to itself should be current directory
            assert rel == "." or rel == os.curdir, f"relpath({repr(abs_path)}, {repr(abs_path)}) = {repr(rel)}, expected '.'"
        except (ValueError, TypeError):
            # Some paths might not work with relpath
            pass
    
    check_relpath_same()


if __name__ == "__main__":
    print("Testing os module edge cases with aggressive inputs...")
    
    print("\n1. Testing splitext with multiple dots...")
    test_splitext_with_multiple_dots()
    print("   ✓ Passed")
    
    print("\n2. Testing normpath with edge cases...")
    test_normpath_with_edge_cases()
    print("   ✓ Passed")
    
    print("\n3. Testing join with absolute paths...")
    test_join_with_absolute_paths()
    print("   ✓ Passed")
    
    print("\n4. Testing commonpath with unicode...")
    test_commonpath_with_unicode()
    print("   ✓ Passed")
    
    print("\n5. Testing split with only separators...")
    test_split_with_only_separators()
    print("   ✓ Passed")
    
    print("\n6. Testing expanduser consistency...")
    test_expanduser_consistency()
    print("   ✓ Passed")
    
    print("\n7. Testing relpath with same path...")
    test_relpath_with_same_path()
    print("   ✓ Passed")
    
    print("\nAll edge case tests passed!")