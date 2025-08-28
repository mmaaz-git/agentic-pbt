import sys
import os
import tempfile
import types

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.register import Registry


def test_prepare_with_non_utf8_file():
    """Test that prepare() fails with non-UTF8 files while auto_register handles them."""
    
    # Create a file with invalid UTF-8 bytes
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
        # These bytes are not valid UTF-8
        f.write(b'\xff\xfe\x00\x00\xde\xad\xbe\xef')
        temp_file = f.name
    
    print(f"Created test file: {temp_file}")
    
    try:
        # Create a module for this file
        module = types.ModuleType('invalid_utf8_module')
        module.__file__ = temp_file
        module.__name__ = 'invalid_utf8_module'
        sys.modules['invalid_utf8_module'] = module
        
        # Test 1: Direct prepare() call
        reg1 = Registry()
        try:
            result = reg1.prepare('invalid_utf8_module')
            print(f"ERROR: prepare() succeeded when it should have failed!")
            print(f"Result: {result}")
            if temp_file in reg1.precache:
                print(f"File was incorrectly cached!")
        except UnicodeDecodeError as e:
            print(f"✓ prepare() correctly raised UnicodeDecodeError: {e}")
        except Exception as e:
            print(f"ERROR: prepare() raised unexpected error: {type(e).__name__}: {e}")
        
        # Test 2: auto_register() call  
        reg2 = Registry()
        # auto_register should handle the error gracefully
        try:
            # Use a filter that matches our file
            sniffer = reg2.auto_register(filter=lambda x: True)
            print(f"✓ auto_register() handled the file gracefully")
            
            # The file should NOT be in precache since it couldn't be read
            if temp_file in reg2.precache:
                print(f"ERROR: Invalid UTF-8 file was cached by auto_register!")
            else:
                print(f"✓ Invalid UTF-8 file was not cached by auto_register")
                
            sniffer.uninstall()
        except Exception as e:
            print(f"ERROR: auto_register() raised error: {type(e).__name__}: {e}")
            
    finally:
        # Clean up
        if 'invalid_utf8_module' in sys.modules:
            del sys.modules['invalid_utf8_module']
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_inconsistent_error_handling():
    """Demonstrate the inconsistency in error handling between prepare() and auto_register()."""
    
    print("\n=== Testing Error Handling Inconsistency ===")
    print("prepare() does NOT catch UnicodeDecodeError")
    print("auto_register() DOES catch UnicodeDecodeError")
    print("This inconsistency can lead to unexpected crashes.\n")
    
    # Create a Python file with Latin-1 encoding that's not valid UTF-8
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
        # Write Python code with Latin-1 characters
        f.write(b'# -*- coding: latin-1 -*-\n')
        f.write(b'# Author: Fran\xe7ois\n')  # \xe7 is ç in Latin-1, invalid UTF-8
        f.write(b'x = "caf\xe9"\n')  # \xe9 is é in Latin-1, invalid UTF-8
        temp_file = f.name
    
    print(f"Created Latin-1 encoded file: {temp_file}")
    
    try:
        module = types.ModuleType('latin1_module')
        module.__file__ = temp_file
        module.__name__ = 'latin1_module'
        sys.modules['latin1_module'] = module
        
        # Test direct prepare()
        reg1 = Registry()
        try:
            reg1.prepare('latin1_module')
            print("ERROR: prepare() succeeded with Latin-1 file!")
        except UnicodeDecodeError:
            print("✓ prepare() failed with UnicodeDecodeError (no error handling)")
            
        # Test auto_register()
        reg2 = Registry()
        try:
            sniffer = reg2.auto_register(filter=lambda x: True)
            print("✓ auto_register() succeeded (has error handling)")
            sniffer.uninstall()
        except UnicodeDecodeError:
            print("ERROR: auto_register() didn't catch UnicodeDecodeError!")
            
    finally:
        if 'latin1_module' in sys.modules:
            del sys.modules['latin1_module']
        if os.path.exists(temp_file):
            os.unlink(temp_file)


if __name__ == "__main__":
    test_prepare_with_non_utf8_file()
    test_inconsistent_error_handling()