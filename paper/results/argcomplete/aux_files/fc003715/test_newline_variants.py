#!/usr/bin/env python3
"""
Test append_to_config_file with various newline-related inputs.
"""

import os
import tempfile
from unittest.mock import patch
import argcomplete.scripts.activate_global_python_argcomplete as activate_script

def test_newline_variant(shellcode, description):
    """Test idempotence with a specific shellcode."""
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        filepath = f.name
    
    try:
        with patch.object(activate_script, 'get_consent', return_value=True):
            # Append twice
            activate_script.append_to_config_file(filepath, shellcode)
            
            with open(filepath, 'rb') as f:
                content_after_first = f.read()
            
            activate_script.append_to_config_file(filepath, shellcode)
            
            with open(filepath, 'rb') as f:
                content_after_second = f.read()
            
            is_idempotent = (content_after_first == content_after_second)
            
            if is_idempotent:
                print(f"✓ {description}: Idempotent")
            else:
                print(f"✗ {description}: NOT idempotent!")
                print(f"  First:  {repr(content_after_first)}")
                print(f"  Second: {repr(content_after_second)}")
            
            return is_idempotent
    
    finally:
        os.unlink(filepath)

if __name__ == "__main__":
    test_cases = [
        ('\r', 'Carriage return'),
        ('\n', 'Line feed'),
        ('\r\n', 'CRLF (Windows newline)'),
        ('\n\r', 'LF+CR'),
        ('test\r', 'Text ending with CR'),
        ('test\n', 'Text ending with LF'),
        ('test\r\n', 'Text ending with CRLF'),
        ('\rtest', 'Text starting with CR'),
        ('test\rmore', 'Text with CR in middle'),
    ]
    
    failures = []
    for shellcode, desc in test_cases:
        if not test_newline_variant(shellcode, desc):
            failures.append((shellcode, desc))
    
    if failures:
        print(f"\n{len(failures)} test(s) failed - idempotence violated for:")
        for shellcode, desc in failures:
            print(f"  - {desc}: {repr(shellcode)}")
    else:
        print("\nAll tests passed!")