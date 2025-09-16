"""Property-based tests for Python os module using Hypothesis"""

import os
import os.path
import sys
import math
from hypothesis import given, strategies as st, assume, settings
import tempfile
import uuid


# Strategy for generating valid path strings
# We avoid null bytes and control characters that could cause issues
path_chars = st.text(
    alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters='\x00'),
    min_size=0,
    max_size=100
)

# Strategy for simple paths without null bytes
simple_paths = st.text(min_size=0, max_size=200).filter(lambda x: '\x00' not in x)

# Strategy for non-empty paths 
nonempty_paths = st.text(min_size=1, max_size=200).filter(lambda x: '\x00' not in x)


def test_normpath_idempotence():
    """Test that normpath is idempotent: normpath(normpath(x)) == normpath(x)"""
    @given(simple_paths)
    def check_idempotence(path):
        # normpath documentation says it normalizes a path
        norm1 = os.path.normpath(path)
        norm2 = os.path.normpath(norm1)
        assert norm1 == norm2, f"normpath not idempotent: {repr(path)} -> {repr(norm1)} -> {repr(norm2)}"
    
    check_idempotence()


def test_splitext_round_trip():
    """Test that splitext preserves the original path: root + ext == path"""
    @given(simple_paths)
    def check_round_trip(path):
        # splitext documentation says it splits the extension from a pathname
        root, ext = os.path.splitext(path)
        rejoined = root + ext
        assert rejoined == path, f"splitext round-trip failed: {repr(path)} != {repr(rejoined)}"
    
    check_round_trip()


def test_split_basename_dirname_consistency():
    """Test that split, basename, and dirname are consistent"""
    @given(simple_paths)
    def check_consistency(path):
        # The documentation states split returns (head, tail) where head is dirname and tail is basename
        head, tail = os.path.split(path)
        dirname_result = os.path.dirname(path)
        basename_result = os.path.basename(path)
        
        assert head == dirname_result, f"split head != dirname for {repr(path)}: {repr(head)} != {repr(dirname_result)}"
        assert tail == basename_result, f"split tail != basename for {repr(path)}: {repr(tail)} != {repr(basename_result)}"
    
    check_consistency()


def test_join_split_relationship():
    """Test relationship between join and split - with normalization"""
    @given(simple_paths)
    def check_join_split(path):
        # Skip empty paths as they have special behavior
        if not path:
            return
            
        head, tail = os.path.split(path)
        
        # Special case: if tail is empty (path ends with separator), join won't preserve trailing slash
        if tail:
            rejoined = os.path.join(head, tail)
            # The rejoined path should represent the same location, though may be normalized
            # We normalize both to check equivalence
            assert os.path.normpath(rejoined) == os.path.normpath(path), \
                f"join(split({repr(path)})) not equivalent: {repr(rejoined)} != {repr(path)}"
    
    check_join_split()


def test_commonpath_prefix_invariant():
    """Test that commonpath returns a path that is a prefix of all input paths"""
    # Generate lists of absolute paths to ensure they have a common base
    @given(st.lists(
        st.tuples(
            st.just("/base"),  # Common prefix
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz/", min_size=1, max_size=20)
        ),
        min_size=2,
        max_size=10
    ))
    def check_commonpath(path_tuples):
        # Build paths with common base
        paths = [base + "/" + suffix for base, suffix in path_tuples]
        
        try:
            common = os.path.commonpath(paths)
            
            # The common path should be a prefix of all normalized paths
            for p in paths:
                # Need to normalize and handle trailing slashes
                norm_p = os.path.normpath(p)
                norm_common = os.path.normpath(common)
                
                # Check that the normalized path starts with the normalized common path
                # Add separator to ensure we match full path components
                if not norm_p.startswith(norm_common):
                    # Check if they're the same (edge case)
                    assert norm_p == norm_common, \
                        f"commonpath {repr(common)} is not a prefix of {repr(p)}"
                elif norm_p != norm_common:
                    # Ensure the next character is a separator (not matching partial component)
                    assert norm_p[len(norm_common)] == os.sep, \
                        f"commonpath {repr(common)} matches partial component in {repr(p)}"
                        
        except ValueError:
            # commonpath raises ValueError for mix of absolute/relative paths - that's expected
            pass
    
    check_commonpath()


def test_abspath_idempotence():
    """Test that abspath is idempotent"""
    @given(simple_paths)
    def check_abspath_idempotent(path):
        # abspath documentation says it returns an absolute path
        try:
            abs1 = os.path.abspath(path)
            abs2 = os.path.abspath(abs1)
            assert abs1 == abs2, f"abspath not idempotent: {repr(path)} -> {repr(abs1)} -> {repr(abs2)}"
        except (OSError, ValueError):
            # Some invalid paths might raise errors
            pass
    
    check_abspath_idempotent()


def test_isabs_abspath_consistency():
    """Test that abspath always returns an absolute path"""
    @given(simple_paths)
    def check_abs_consistency(path):
        try:
            abs_path = os.path.abspath(path)
            assert os.path.isabs(abs_path), f"abspath({repr(path)}) = {repr(abs_path)} is not absolute"
        except (OSError, ValueError):
            pass
    
    check_abs_consistency()


def test_environ_round_trip():
    """Test that setting and getting environment variables is consistent"""
    @given(
        st.text(alphabet=st.characters(min_codepoint=1, blacklist_categories=("Cc", "Cs")), min_size=1, max_size=50),
        st.text(alphabet=st.characters(min_codepoint=1, blacklist_categories=("Cc", "Cs")), min_size=0, max_size=100)
    )
    def check_environ_round_trip(key, value):
        # Ensure the key doesn't contain '=' and doesn't start with a digit
        assume('=' not in key)
        assume(not key[0].isdigit())
        assume('\x00' not in key and '\x00' not in value)
        
        # Use a unique prefix to avoid conflicts
        test_key = f"HYPOTHESIS_TEST_{uuid.uuid4().hex[:8]}_{key}"
        
        # Ensure we start clean
        original = os.environ.get(test_key)
        
        try:
            # Set the value
            os.environ[test_key] = value
            
            # Get it back
            retrieved = os.environ.get(test_key)
            
            assert retrieved == value, f"Environment variable round-trip failed: set {repr(value)}, got {repr(retrieved)}"
            
        finally:
            # Clean up
            if original is None:
                os.environ.pop(test_key, None)
            else:
                os.environ[test_key] = original
    
    check_environ_round_trip()


def test_dup_creates_different_fd():
    """Test that os.dup creates a different file descriptor"""
    # This is more of a behavioral test than a property test
    def check_dup():
        with tempfile.TemporaryFile() as f:
            fd1 = f.fileno()
            fd2 = os.dup(fd1)
            try:
                assert fd1 != fd2, f"dup({fd1}) returned the same fd: {fd2}"
                # Both should be valid file descriptors
                os.fstat(fd1)  # Should not raise
                os.fstat(fd2)  # Should not raise
            finally:
                os.close(fd2)
    
    # Run it multiple times to ensure consistency
    for _ in range(10):
        check_dup()


if __name__ == "__main__":
    print("Testing os module properties with Hypothesis...")
    
    print("\n1. Testing normpath idempotence...")
    test_normpath_idempotence()
    print("   ✓ Passed")
    
    print("\n2. Testing splitext round-trip...")
    test_splitext_round_trip()
    print("   ✓ Passed")
    
    print("\n3. Testing split/basename/dirname consistency...")
    test_split_basename_dirname_consistency()
    print("   ✓ Passed")
    
    print("\n4. Testing join/split relationship...")
    test_join_split_relationship()
    print("   ✓ Passed")
    
    print("\n5. Testing commonpath prefix invariant...")
    test_commonpath_prefix_invariant()
    print("   ✓ Passed")
    
    print("\n6. Testing abspath idempotence...")
    test_abspath_idempotence()
    print("   ✓ Passed")
    
    print("\n7. Testing isabs/abspath consistency...")
    test_isabs_abspath_consistency()
    print("   ✓ Passed")
    
    print("\n8. Testing environment variable round-trip...")
    test_environ_round_trip()
    print("   ✓ Passed")
    
    print("\n9. Testing dup creates different fd...")
    test_dup_creates_different_fd()
    print("   ✓ Passed")
    
    print("\nAll property tests passed!")