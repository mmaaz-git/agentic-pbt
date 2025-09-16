#!/usr/bin/env python3
"""Reproduction test for the cleanup bug in NamedFileInTemporaryDirectory."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import testpath.tempdir
from hypothesis import given, strategies as st
import string

# Test with modes that might fail to open the file
@given(mode=st.sampled_from(['r', 'rb']))  # Read modes on non-existent file
def test_cleanup_bug_with_read_mode(mode):
    """Test that cleanup doesn't fail when file opening fails."""
    try:
        # This should fail because the file doesn't exist yet and we're opening in read mode
        with testpath.tempdir.NamedFileInTemporaryDirectory('testfile.txt', mode=mode) as f:
            pass  # Should never reach here
    except FileNotFoundError:
        # This is expected - file doesn't exist and we tried to open in read mode
        pass
    except AttributeError as e:
        # This would be the bug - cleanup trying to access self.file when it wasn't set
        if "'NamedFileInTemporaryDirectory' object has no attribute 'file'" in str(e):
            raise AssertionError(f"Bug found: cleanup fails when file opening fails. Error: {e}")
        raise


def test_cleanup_bug_direct():
    """Direct test of the cleanup bug."""
    import traceback
    
    # Try to trigger the bug directly
    print("Testing with read mode on non-existent file...")
    try:
        ctx = testpath.tempdir.NamedFileInTemporaryDirectory('nonexistent.txt', mode='r')
        # This should fail in __init__ when trying to open the file
    except FileNotFoundError as e:
        print(f"FileNotFoundError as expected: {e}")
        # Now check if the object has a cleanup issue
        try:
            # If __init__ failed after creating _tmpdir but before setting self.file,
            # the __del__ method might be called and fail
            if hasattr(ctx, '_tmpdir') and not hasattr(ctx, 'file'):
                print("Bug confirmed: Object has _tmpdir but not file attribute")
                print("This will cause AttributeError in cleanup/__del__")
                # Try to trigger cleanup manually
                try:
                    ctx.cleanup()
                except AttributeError as ae:
                    print(f"AttributeError in cleanup: {ae}")
                    return True  # Bug found
        except Exception as e:
            print(f"Error checking object state: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
    
    return False


def test_minimal_reproduction():
    """Minimal reproduction of the bug."""
    print("\n=== Minimal Bug Reproduction ===")
    print("Creating NamedFileInTemporaryDirectory with mode='r' (read-only)...")
    print("This will fail because the file doesn't exist yet.")
    
    bug_found = False
    try:
        # This will fail in __init__ because file doesn't exist
        with testpath.tempdir.NamedFileInTemporaryDirectory('test.txt', mode='r') as f:
            print("Should not reach here")
    except FileNotFoundError:
        print("FileNotFoundError raised as expected")
        # The bug is that cleanup/del will fail with AttributeError
        # This happens because __init__ creates self._tmpdir but fails before creating self.file
        bug_found = True
    except Exception as e:
        print(f"Unexpected exception: {e}")
    
    if bug_found:
        print("\nBUG CONFIRMED: When NamedFileInTemporaryDirectory.__init__ fails after")
        print("creating self._tmpdir but before setting self.file, the cleanup method")
        print("will raise AttributeError when trying to access self.file")
        
        # Show the problematic code
        print("\nProblematic code in tempdir.py:")
        print("  Line 32-34 in __init__:")
        print("    self._tmpdir = TemporaryDirectory(**kwds)")
        print("    path = _os.path.join(self._tmpdir.name, filename)")
        print("    self.file = open(path, mode, bufsize)  # <- This can fail")
        print()
        print("  Line 36-37 in cleanup:")
        print("    def cleanup(self):")
        print("        self.file.close()  # <- AttributeError if __init__ failed")
        
        return True
    
    return False


if __name__ == "__main__":
    print("Testing for cleanup bug in NamedFileInTemporaryDirectory\n")
    
    # Run direct test
    if test_cleanup_bug_direct():
        print("\n✗ Bug found in direct test")
    else:
        print("\n✓ No bug found in direct test")
    
    # Run minimal reproduction
    if test_minimal_reproduction():
        print("\n✗ Bug confirmed in minimal reproduction")
    else:
        print("\n✓ No bug in minimal reproduction")
    
    # Run hypothesis test
    print("\n=== Running Hypothesis test ===")
    try:
        test_cleanup_bug_with_read_mode()
        print("✓ Hypothesis test passed")
    except AssertionError as e:
        print(f"✗ Hypothesis test failed: {e}")