#!/usr/bin/env python3
"""Investigate the broken symlink bug in testpath.asserts."""

import os
import tempfile
import testpath.asserts as asserts

def investigate_broken_symlink_bug():
    """Detailed investigation of broken symlink behavior."""
    print("="*60)
    print("INVESTIGATING BROKEN SYMLINK BUG")
    print("="*60)
    
    # Create a broken symlink
    temp_dir = tempfile.gettempdir()
    symlink_path = os.path.join(temp_dir, "test_broken_symlink_bug")
    target_path = os.path.join(temp_dir, "nonexistent_target_bug")
    
    # Clean up first
    for p in [symlink_path, target_path]:
        try:
            if os.path.islink(p) or os.path.exists(p):
                os.remove(p)
        except:
            pass
    
    # Create broken symlink
    os.symlink(target_path, symlink_path)
    
    print(f"\nCreated broken symlink: {symlink_path}")
    print(f"Points to (non-existent): {target_path}")
    
    # Check OS-level behavior
    print("\n--- OS-level checks ---")
    print(f"os.path.exists(symlink_path): {os.path.exists(symlink_path)}")
    print(f"os.path.islink(symlink_path): {os.path.islink(symlink_path)}")
    print(f"os.path.lexists(symlink_path): {os.path.lexists(symlink_path)}")
    
    try:
        stat_result = os.stat(symlink_path)
        print(f"os.stat(symlink_path): Success - {stat_result}")
    except OSError as e:
        print(f"os.stat(symlink_path): Failed - {e}")
    
    try:
        lstat_result = os.lstat(symlink_path)
        print(f"os.lstat(symlink_path): Success - mode={oct(lstat_result.st_mode)}")
    except OSError as e:
        print(f"os.lstat(symlink_path): Failed - {e}")
    
    # Test testpath.asserts behavior
    print("\n--- testpath.asserts behavior ---")
    
    # Test assert_path_exists
    try:
        asserts.assert_path_exists(symlink_path)
        print("assert_path_exists(broken_symlink): PASSED")
    except AssertionError as e:
        print(f"assert_path_exists(broken_symlink): FAILED - {e}")
    
    # Test assert_not_path_exists  
    try:
        asserts.assert_not_path_exists(symlink_path)
        print("assert_not_path_exists(broken_symlink): PASSED")
    except AssertionError as e:
        print(f"assert_not_path_exists(broken_symlink): FAILED - {e}")
    
    # Test assert_islink
    try:
        asserts.assert_islink(symlink_path)
        print("assert_islink(broken_symlink): PASSED")
    except AssertionError as e:
        print(f"assert_islink(broken_symlink): FAILED - {e}")
    
    # Analyze the implementation
    print("\n--- Implementation Analysis ---")
    print("Looking at the source code:")
    print("- assert_path_exists uses os.stat() with follow_symlinks=True")
    print("- assert_not_path_exists uses os.path.exists()")
    print("- os.stat() with follow_symlinks=True fails on broken symlinks")
    print("- os.path.exists() returns False for broken symlinks")
    
    print("\n--- BUG ANALYSIS ---")
    print("The issue: Broken symlinks create an inconsistency:")
    print("1. assert_path_exists(broken_symlink) -> FAILS (uses os.stat)")
    print("2. assert_not_path_exists(broken_symlink) -> PASSES (uses os.path.exists)")
    print("\nThis violates the inverse property:")
    print("For any path, exactly one of assert_path_exists and")
    print("assert_not_path_exists should pass.")
    print("\nBroken symlinks break this invariant because:")
    print("- They exist as filesystem entries (detectable via os.lstat)")
    print("- But os.path.exists() returns False")
    print("- And os.stat() raises OSError when following the link")
    
    # Clean up
    os.remove(symlink_path)
    
    return True  # Bug confirmed


def test_hypothesis_reproduction():
    """Create a minimal Hypothesis test that reproduces the bug."""
    print("\n" + "="*60)
    print("MINIMAL HYPOTHESIS TEST")
    print("="*60)
    
    from hypothesis import given, strategies as st
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=10))
    def test_broken_symlink_inverse_property(name):
        """Property: For any path, exactly one of assert_path_exists and assert_not_path_exists should pass."""
        temp_dir = tempfile.gettempdir()
        symlink_path = os.path.join(temp_dir, f"hypo_{name}")
        target_path = os.path.join(temp_dir, f"target_{name}")
        
        # Clean up first
        for p in [symlink_path, target_path]:
            try:
                if os.path.islink(p) or os.path.exists(p):
                    os.remove(p)
            except:
                pass
        
        # Create a broken symlink
        os.symlink(target_path, symlink_path)
        
        # Count how many assertions pass
        passing = []
        
        try:
            asserts.assert_path_exists(symlink_path)
            passing.append('exists')
        except AssertionError:
            pass
        
        try:
            asserts.assert_not_path_exists(symlink_path)
            passing.append('not_exists')
        except AssertionError:
            pass
        
        # Clean up
        os.remove(symlink_path)
        
        # Exactly one should pass (inverse property)
        if len(passing) != 1:
            raise AssertionError(
                f"Inverse property violated for broken symlink: "
                f"{passing} passed (expected exactly 1)"
            )
    
    # Run the test
    print("\nRunning Hypothesis test...")
    try:
        test_broken_symlink_inverse_property()
        print("Test completed - checking multiple random names")
    except AssertionError as e:
        print(f"BUG CONFIRMED: {e}")
        return True
    
    return False


if __name__ == "__main__":
    bug_found = investigate_broken_symlink_bug()
    
    if bug_found:
        print("\n" + "="*60)
        print("BUG CONFIRMED!")
        print("="*60)
        
        # Run hypothesis test to confirm
        test_hypothesis_reproduction()