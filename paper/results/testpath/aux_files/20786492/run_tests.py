#!/usr/bin/env python3
"""Run property-based tests for testpath.asserts module."""

import sys
import os
import stat
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hypothesis import given, strategies as st, settings
import testpath.asserts as asserts

def test_exists_inverse_simple():
    """Simple test for assert_path_exists and assert_not_path_exists inverse property."""
    print("Testing exists inverse property...")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    # Path exists - assert_path_exists should pass, assert_not_path_exists should fail
    try:
        asserts.assert_path_exists(temp_path)
        print("✓ assert_path_exists passes for existing file")
    except AssertionError:
        print("✗ BUG: assert_path_exists failed for existing file")
    
    try:
        asserts.assert_not_path_exists(temp_path)
        print("✗ BUG: assert_not_path_exists passed for existing file")
    except AssertionError:
        print("✓ assert_not_path_exists fails for existing file")
    
    # Remove the file
    os.remove(temp_path)
    
    # Path doesn't exist - assert_path_exists should fail, assert_not_path_exists should pass
    try:
        asserts.assert_path_exists(temp_path)
        print("✗ BUG: assert_path_exists passed for non-existent file")
    except AssertionError:
        print("✓ assert_path_exists fails for non-existent file")
    
    try:
        asserts.assert_not_path_exists(temp_path)
        print("✓ assert_not_path_exists passes for non-existent file")
    except AssertionError:
        print("✗ BUG: assert_not_path_exists failed for non-existent file")


def test_broken_symlink_behavior():
    """Test behavior with broken symlinks."""
    print("\nTesting broken symlink behavior...")
    
    # Create a broken symlink
    temp_dir = tempfile.gettempdir()
    symlink_path = os.path.join(temp_dir, "test_broken_symlink")
    target_path = os.path.join(temp_dir, "nonexistent_target")
    
    # Clean up first
    try:
        if os.path.islink(symlink_path):
            os.remove(symlink_path)
    except:
        pass
    
    # Create broken symlink
    os.symlink(target_path, symlink_path)
    
    print(f"Created broken symlink: {symlink_path} -> {target_path}")
    print(f"os.path.exists(symlink_path): {os.path.exists(symlink_path)}")
    print(f"os.path.islink(symlink_path): {os.path.islink(symlink_path)}")
    
    # Test assert_path_exists on broken symlink
    try:
        asserts.assert_path_exists(symlink_path)
        print("✓ assert_path_exists passes for broken symlink")
    except AssertionError as e:
        print(f"✗ assert_path_exists fails for broken symlink: {e}")
    
    # Test assert_not_path_exists on broken symlink
    try:
        asserts.assert_not_path_exists(symlink_path)
        print("✗ assert_not_path_exists passes for broken symlink")
    except AssertionError as e:
        print(f"✓ assert_not_path_exists fails for broken symlink: {e}")
    
    # Clean up
    os.remove(symlink_path)


def test_file_type_mutual_exclusivity():
    """Test that file types are mutually exclusive."""
    print("\nTesting file type mutual exclusivity...")
    
    # Create a regular file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        file_path = f.name
        f.write(b"test")
    
    # Create a directory
    dir_path = tempfile.mkdtemp()
    
    # Test file
    print(f"Testing regular file: {file_path}")
    file_types = []
    try:
        asserts.assert_isfile(file_path)
        file_types.append("file")
    except:
        pass
    try:
        asserts.assert_isdir(file_path)
        file_types.append("dir")
    except:
        pass
    try:
        asserts.assert_islink(file_path)
        file_types.append("link")
    except:
        pass
    
    print(f"File matched types: {file_types}")
    if len(file_types) != 1:
        print(f"✗ BUG: File matched {len(file_types)} types instead of 1")
    else:
        print("✓ File matched exactly 1 type")
    
    # Test directory
    print(f"\nTesting directory: {dir_path}")
    dir_types = []
    try:
        asserts.assert_isfile(dir_path)
        dir_types.append("file")
    except:
        pass
    try:
        asserts.assert_isdir(dir_path)
        dir_types.append("dir")
    except:
        pass
    try:
        asserts.assert_islink(dir_path)
        dir_types.append("link")
    except:
        pass
    
    print(f"Directory matched types: {dir_types}")
    if len(dir_types) != 1:
        print(f"✗ BUG: Directory matched {len(dir_types)} types instead of 1")
    else:
        print("✓ Directory matched exactly 1 type")
    
    # Clean up
    os.remove(file_path)
    os.rmdir(dir_path)


def test_not_functions_inverse():
    """Test that assert_not_isX functions are inverses of assert_isX."""
    print("\nTesting not-functions inverse property...")
    
    # Create a test file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        file_path = f.name
    
    # Test assert_isfile and assert_not_isfile
    print(f"Testing file: {file_path}")
    
    try:
        asserts.assert_isfile(file_path)
        is_file = True
        print("✓ assert_isfile passes")
    except AssertionError:
        is_file = False
        print("✗ assert_isfile fails")
    
    try:
        asserts.assert_not_isfile(file_path)
        not_is_file = True
        print("✗ assert_not_isfile passes")
    except AssertionError:
        not_is_file = False
        print("✓ assert_not_isfile fails")
    
    if is_file == not_is_file:
        print("✗ BUG: assert_isfile and assert_not_isfile both returned same result!")
    else:
        print("✓ assert_isfile and assert_not_isfile are proper inverses")
    
    # Clean up
    os.remove(file_path)


def test_custom_message_preservation():
    """Test that custom error messages are preserved."""
    print("\nTesting custom message preservation...")
    
    custom_msg = "This is my custom error message!"
    non_existent = "/tmp/definitely_does_not_exist_xyz123"
    
    # Make sure it doesn't exist
    try:
        os.remove(non_existent)
    except:
        pass
    
    # Test custom message is preserved
    try:
        asserts.assert_path_exists(non_existent, msg=custom_msg)
        print("✗ BUG: assert_path_exists didn't raise for non-existent path")
    except AssertionError as e:
        if str(e) == custom_msg:
            print("✓ Custom message preserved exactly")
        else:
            print(f"✗ BUG: Custom message not preserved")
            print(f"  Expected: {custom_msg}")
            print(f"  Got: {str(e)}")


def test_symlink_follow_behavior():
    """Test symlink follow_symlinks parameter behavior."""
    print("\nTesting symlink follow_symlinks parameter...")
    
    temp_dir = tempfile.gettempdir()
    target_file = os.path.join(temp_dir, "target_file")
    symlink_path = os.path.join(temp_dir, "test_symlink")
    
    # Clean up first
    for p in [symlink_path, target_file]:
        try:
            if os.path.islink(p) or os.path.exists(p):
                os.remove(p)
        except:
            pass
    
    # Create a file and symlink to it
    with open(target_file, 'w') as f:
        f.write('content')
    os.symlink(target_file, symlink_path)
    
    print(f"Created symlink: {symlink_path} -> {target_file}")
    
    # Test with follow_symlinks=True (should treat as file)
    try:
        asserts.assert_isfile(symlink_path, follow_symlinks=True)
        print("✓ With follow_symlinks=True, symlink treated as file")
    except AssertionError:
        print("✗ BUG: With follow_symlinks=True, symlink not treated as file")
    
    # Test with follow_symlinks=False (should NOT treat as file)
    try:
        asserts.assert_isfile(symlink_path, follow_symlinks=False)
        print("✗ BUG: With follow_symlinks=False, symlink still treated as file")
    except AssertionError:
        print("✓ With follow_symlinks=False, symlink not treated as file")
    
    # Test islink (should always detect symlink)
    try:
        asserts.assert_islink(symlink_path)
        print("✓ assert_islink detects symlink")
    except AssertionError:
        print("✗ BUG: assert_islink doesn't detect symlink")
    
    # Clean up
    os.remove(symlink_path)
    os.remove(target_file)


def test_assert_not_functions_with_nonexistent_paths():
    """Test assert_not_* functions with paths that don't exist."""
    print("\nTesting assert_not_* functions with non-existent paths...")
    
    non_existent = "/tmp/this_definitely_does_not_exist_abc123xyz"
    
    # Make sure it doesn't exist
    try:
        os.remove(non_existent)
    except:
        pass
    
    # According to the code, assert_not_isfile requires the path to exist
    # Let's test this
    print(f"Testing non-existent path: {non_existent}")
    
    try:
        asserts.assert_not_isfile(non_existent)
        print("✗ assert_not_isfile passed for non-existent path")
    except AssertionError as e:
        print(f"✓ assert_not_isfile failed for non-existent path: {e}")
    
    try:
        asserts.assert_not_isdir(non_existent)
        print("✗ assert_not_isdir passed for non-existent path")
    except AssertionError as e:
        print(f"✓ assert_not_isdir failed for non-existent path: {e}")
    
    try:
        asserts.assert_not_islink(non_existent)
        print("✗ assert_not_islink passed for non-existent path")
    except AssertionError as e:
        print(f"✓ assert_not_islink failed for non-existent path: {e}")


if __name__ == "__main__":
    print("="*60)
    print("Running property-based tests for testpath.asserts")
    print("="*60)
    
    test_exists_inverse_simple()
    test_broken_symlink_behavior()
    test_file_type_mutual_exclusivity()
    test_not_functions_inverse()
    test_custom_message_preservation()
    test_symlink_follow_behavior()
    test_assert_not_functions_with_nonexistent_paths()
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)