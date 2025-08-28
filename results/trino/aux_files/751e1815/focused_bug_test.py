#!/usr/bin/env python3
"""
Focused test to identify specific bug in trino.dbapi bytes formatting
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

print("Testing trino.dbapi._format_prepared_param for bytes formatting bug...")
print("=" * 70)

from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

# Create cursor instance
mock_connection = Mock(spec=Connection)
cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)

# Test various byte sequences
test_cases = [
    (b'\xAB\xCD\xEF', "Should format as X'ABCDEF' (uppercase)"),
    (b'\x00\x01\xFF', "Should format as X'0001FF' (uppercase with padding)"),
    (b'', "Empty bytes should format as X''"),
    (b'\xde\xad\xbe\xef', "Should format as X'DEADBEEF' (uppercase)"),
]

print("\nTesting bytes formatting:")
print("-" * 70)

bug_found = False

for test_bytes, description in test_cases:
    result = cursor._format_prepared_param(test_bytes)
    hex_str = test_bytes.hex()
    
    print(f"\nInput: {test_bytes!r}")
    print(f"Description: {description}")
    print(f"Result: {result}")
    
    # Check if the hex is lowercase (which is what hex() returns)
    if test_bytes and hex_str.lower() in result.lower():
        # Check if it's actually lowercase in the result
        hex_part = result[2:-1]  # Extract hex part between X' and '
        if hex_part and hex_part != hex_part.upper():
            print(f">>> BUG DETECTED: Hex formatted as lowercase!")
            print(f"    Expected: X'{hex_str.upper()}'")
            print(f"    Got:      {result}")
            bug_found = True
        else:
            print(f"    Status: OK (uppercase hex)")
    else:
        print(f"    Status: OK")

print("\n" + "=" * 70)

if bug_found:
    print("\nBUG SUMMARY:")
    print("-" * 70)
    print("The _format_prepared_param method in trino.dbapi uses param.hex()")
    print("which returns lowercase hexadecimal. However, SQL standard and many")
    print("databases expect uppercase hex literals (X'ABCD' not X'abcd').")
    print("\nThis could cause issues when interfacing with systems that are")
    print("case-sensitive about hex literals.")
    print("\nAffected code: Line 546 in /root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages/trino/dbapi.py")
    print("Current:  return \"X'%s'\" % param.hex()")
    print("Fix:      return \"X'%s'\" % param.hex().upper()")
else:
    print("\nNo bugs found in bytes formatting.")

print("=" * 70)