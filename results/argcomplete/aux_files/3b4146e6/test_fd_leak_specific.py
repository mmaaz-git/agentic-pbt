import sys
import os
import gc
import argcomplete.io


def test_mute_stdout_leaks_file_descriptors():
    """Demonstrate that mute_stdout() leaks file descriptors"""
    
    # Get list of open file descriptors before
    fds_before = set(os.listdir('/proc/self/fd'))
    
    # Use mute_stdout
    with argcomplete.io.mute_stdout():
        print("test")
    
    # Force garbage collection to ensure any closed files are cleaned up
    gc.collect()
    
    # Get list of open file descriptors after
    fds_after = set(os.listdir('/proc/self/fd'))
    
    # Check if new file descriptors were left open
    leaked_fds = fds_after - fds_before
    
    if leaked_fds:
        # Verify that the leaked FDs point to /dev/null
        for fd in leaked_fds:
            try:
                link = os.readlink(f'/proc/self/fd/{fd}')
                print(f"Leaked FD {fd} points to: {link}")
                if link == '/dev/null':
                    print(f"CONFIRMED: File descriptor {fd} leaked, pointing to /dev/null")
                    return True
            except:
                pass
    
    return False


def test_mute_stderr_does_not_leak():
    """Verify that mute_stderr() properly closes file descriptors"""
    
    # Get list of open file descriptors before
    fds_before = set(os.listdir('/proc/self/fd'))
    
    # Use mute_stderr
    with argcomplete.io.mute_stderr():
        print("test", file=sys.stderr)
    
    # Force garbage collection
    gc.collect()
    
    # Get list of open file descriptors after
    fds_after = set(os.listdir('/proc/self/fd'))
    
    # Check if new file descriptors were left open
    leaked_fds = fds_after - fds_before
    
    if leaked_fds:
        for fd in leaked_fds:
            try:
                link = os.readlink(f'/proc/self/fd/{fd}')
                if link == '/dev/null':
                    print(f"ERROR: mute_stderr also leaked FD {fd}")
                    return False
            except:
                pass
    
    print("mute_stderr correctly closes file descriptors")
    return True


if __name__ == "__main__":
    print("Testing file descriptor leak in mute_stdout()...")
    if test_mute_stdout_leaks_file_descriptors():
        print("\n✗ BUG FOUND: mute_stdout() leaks file descriptors!")
    else:
        print("\n✓ No leak detected in mute_stdout()")
    
    print("\n" + "="*50)
    print("\nTesting mute_stderr() for comparison...")
    test_mute_stderr_does_not_leak()