#!/usr/bin/env python3
"""
Minimal reproduction of the append_to_config_file idempotence bug.
"""

import os
import tempfile
from unittest.mock import patch
import argcomplete.scripts.activate_global_python_argcomplete as activate_script

def reproduce_bug():
    """Reproduce the idempotence violation with carriage return."""
    
    # Create a temp file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write("")  # Empty initial content
        filepath = f.name
    
    print(f"Testing with shellcode='\\r' (carriage return)")
    print(f"File: {filepath}")
    
    try:
        with patch.object(activate_script, 'get_consent', return_value=True):
            # First append
            print("\n--- First append ---")
            activate_script.append_to_config_file(filepath, '\r')
            
            with open(filepath, 'rb') as f:
                content_after_first = f.read()
            print(f"Content after first append (bytes): {repr(content_after_first)}")
            
            # Second append (should be idempotent)
            print("\n--- Second append ---")
            activate_script.append_to_config_file(filepath, '\r')
            
            with open(filepath, 'rb') as f:
                content_after_second = f.read()
            print(f"Content after second append (bytes): {repr(content_after_second)}")
            
            # Check if idempotent
            if content_after_first == content_after_second:
                print("\n✓ IDEMPOTENT: Content unchanged after second append")
            else:
                print("\n✗ BUG: Content changed after second append!")
                print(f"  First:  {repr(content_after_first)}")
                print(f"  Second: {repr(content_after_second)}")
                
            # Check the 'in' operator behavior with '\r'
            print("\n--- Investigating the 'in' check ---")
            with open(filepath, 'r') as f:
                file_content = f.read()
            print(f"File content (text mode): {repr(file_content)}")
            print(f"Is '\\r' in file content? {'\r' in file_content}")
            print(f"Is '\\n' in file content? {'\n' in file_content}")
    
    finally:
        os.unlink(filepath)

if __name__ == "__main__":
    reproduce_bug()