import sys
import os
import argcomplete.io


def test_file_close_behavior():
    """Test whether the file opened for /dev/null is properly closed"""
    
    # Track the file object
    devnull_file = None
    
    # Monkey-patch open to capture the file object
    original_open = open
    opened_files = []
    
    def tracking_open(*args, **kwargs):
        f = original_open(*args, **kwargs)
        opened_files.append(f)
        return f
    
    # Replace open temporarily
    import builtins
    builtins.open = tracking_open
    
    try:
        # Test mute_stdout
        print("\n=== Testing mute_stdout ===")
        with argcomplete.io.mute_stdout():
            print("test")
        
        # Check if the /dev/null file was closed
        for f in opened_files:
            if hasattr(f, 'name') and f.name == os.devnull:
                print(f"File object for {f.name}: closed={f.closed}")
                if not f.closed:
                    print("BUG: File not closed after context manager exits!")
        
        opened_files.clear()
        
        # Test mute_stderr
        print("\n=== Testing mute_stderr ===")
        with argcomplete.io.mute_stderr():
            print("test", file=sys.stderr)
        
        # Check if the /dev/null file was closed
        for f in opened_files:
            if hasattr(f, 'name') and f.name == os.devnull:
                print(f"File object for {f.name}: closed={f.closed}")
                if not f.closed:
                    print("BUG: File not closed after context manager exits!")
                    
    finally:
        # Restore original open
        builtins.open = original_open


def test_exception_handling():
    """Test that files are handled correctly even when exceptions occur"""
    
    print("\n=== Testing exception handling ===")
    
    # Track opened files
    original_open = open
    opened_files = []
    
    def tracking_open(*args, **kwargs):
        f = original_open(*args, **kwargs)
        opened_files.append(f)
        return f
    
    import builtins
    builtins.open = tracking_open
    
    try:
        # Test mute_stdout with exception
        print("\nTesting mute_stdout with exception:")
        try:
            with argcomplete.io.mute_stdout():
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Check file status
        for f in opened_files:
            if hasattr(f, 'name') and f.name == os.devnull:
                print(f"After exception - File {f.name}: closed={f.closed}")
                if not f.closed:
                    print("BUG: File not closed after exception!")
        
        opened_files.clear()
        
        # Test mute_stderr with exception
        print("\nTesting mute_stderr with exception:")
        try:
            with argcomplete.io.mute_stderr():
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Check file status
        for f in opened_files:
            if hasattr(f, 'name') and f.name == os.devnull:
                print(f"After exception - File {f.name}: closed={f.closed}")
                if not f.closed:
                    print("BUG: File not closed after exception!")
                    
    finally:
        builtins.open = original_open


if __name__ == "__main__":
    test_file_close_behavior()
    test_exception_handling()