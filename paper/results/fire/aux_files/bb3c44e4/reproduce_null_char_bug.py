"""Minimal reproduction of null character bug in fire.testutils.ChangeDirectory"""

import os
import tempfile
import fire.testutils

# Test 1: Direct os.chdir with null character
print("Test 1: os.chdir with null character in path")
try:
    os.chdir("/tmp/test\x00dir")
except ValueError as e:
    print(f"  os.chdir raised ValueError: {e}")

print("\n" + "="*50)

# Test 2: ChangeDirectory with null character
print("\nTest 2: ChangeDirectory with null character")
with tempfile.TemporaryDirectory() as tmpdir:
    path_with_null = os.path.join(tmpdir, "test\x00dir", "subdir")
    print(f"  Path: {repr(path_with_null)}")
    
    original_dir = os.getcwd()
    print(f"  Original dir: {original_dir}")
    
    try:
        with fire.testutils.ChangeDirectory(path_with_null):
            print("  Should not reach here")
    except ValueError as e:
        print(f"  ChangeDirectory raised ValueError: {e}")
    except FileNotFoundError as e:
        print(f"  ChangeDirectory raised FileNotFoundError: {e}")
    
    # Check if directory was restored
    current_dir = os.getcwd()
    print(f"  Current dir after error: {current_dir}")
    print(f"  Directory restored: {current_dir == original_dir}")

print("\n" + "="*50)

# Test 3: What happens when exception occurs AFTER chdir succeeds?
print("\nTest 3: Exception handling in ChangeDirectory")
with tempfile.TemporaryDirectory() as tmpdir:
    valid_path = tmpdir
    original_dir = os.getcwd()
    
    try:
        with fire.testutils.ChangeDirectory(valid_path):
            print(f"  Changed to: {os.getcwd()}")
            raise RuntimeError("Test exception")
    except RuntimeError:
        pass
    
    print(f"  After exception, dir is: {os.getcwd()}")
    print(f"  Directory restored: {os.getcwd() == original_dir}")