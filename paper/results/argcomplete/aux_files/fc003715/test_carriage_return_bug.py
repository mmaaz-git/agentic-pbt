#!/usr/bin/env python3
"""
Test to demonstrate the carriage return bug in append_to_config_file.
"""

import os
import tempfile
from unittest.mock import patch
import argcomplete.scripts.activate_global_python_argcomplete as activate_script

def test_carriage_return_bug():
    """Test that demonstrates the idempotence violation with carriage return."""
    
    # Create a temp file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        filepath = f.name
    
    try:
        with patch.object(activate_script, 'get_consent', return_value=True):
            # Append carriage return twice
            activate_script.append_to_config_file(filepath, '\r')
            activate_script.append_to_config_file(filepath, '\r')
            
            # Read the file in binary mode to see actual content
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # The bug: '\r' appears twice instead of once
            count = content.count(b'\r')
            assert count == 1, f"Expected '\\r' to appear once (idempotent), but it appears {count} times"
    
    finally:
        os.unlink(filepath)

if __name__ == "__main__":
    try:
        test_carriage_return_bug()
        print("✓ Test passed: append_to_config_file is idempotent with '\\r'")
    except AssertionError as e:
        print(f"✗ Bug confirmed: {e}")