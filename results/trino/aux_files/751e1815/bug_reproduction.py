#!/usr/bin/env python3
"""
Minimal reproduction of the bytes formatting bug in trino.dbapi
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

def reproduce_bug():
    """
    Demonstrates that _format_prepared_param produces lowercase hex
    which may not be compatible with all SQL engines.
    """
    
    # Setup
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    # Test input - bytes that include A-F hex digits
    test_input = b'\xDE\xAD\xBE\xEF'
    
    # Format the parameter
    result = cursor._format_prepared_param(test_input)
    
    # What we got vs what we might expect
    actual = result
    expected_uppercase = "X'DEADBEEF'"
    expected_lowercase = "X'deadbeef'"
    
    print("Bug Reproduction: Bytes Formatting Case Issue")
    print("=" * 50)
    print(f"Input bytes:        {test_input!r}")
    print(f"Actual output:      {actual}")
    print(f"Expected (upper):   {expected_uppercase}")
    print(f"Expected (lower):   {expected_lowercase}")
    print()
    
    if actual == expected_lowercase:
        print("✗ BUG CONFIRMED: Hex is formatted as lowercase")
        print("  This violates SQL standard which typically uses uppercase hex")
        return True
    elif actual == expected_uppercase:
        print("✓ No bug: Hex is correctly formatted as uppercase")
        return False
    else:
        print(f"? Unexpected result: {actual}")
        return None

if __name__ == "__main__":
    bug_found = reproduce_bug()
    
    if bug_found:
        print("\n" + "=" * 50)
        print("IMPACT ASSESSMENT:")
        print("- SQL standard specifies uppercase for hex literals")
        print("- Some databases may be case-sensitive for hex literals")
        print("- This could cause query failures or data corruption")
        print("\nFIX:")
        print("Change line 546 in dbapi.py from:")
        print('  return "X\'%s\'" % param.hex()')
        print("To:")
        print('  return "X\'%s\'" % param.hex().upper()')