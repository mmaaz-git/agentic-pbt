#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

# Test _format_prepared_param with bytes containing uppercase hex
mock_connection = Mock(spec=Connection)
cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)

# Test case 1: Empty bytes
test_bytes = b''
result = cursor._format_prepared_param(test_bytes)
print(f"Empty bytes: {result}")
expected = "X''"
assert result == expected, f"Expected {expected}, got {result}"

# Test case 2: Simple bytes
test_bytes = b'\x00\x01\x02\xff'
result = cursor._format_prepared_param(test_bytes)
print(f"Simple bytes: {result}")
expected = "X'" + test_bytes.hex().upper() + "'"
print(f"Expected: {expected}")

# The issue is that hex() returns lowercase but we expect uppercase
actual_hex = test_bytes.hex()  # returns '000102ff' 
expected_formatted = "X'" + actual_hex.upper() + "'"  # Should be 'X'000102FF''

if result != expected_formatted:
    print(f"FOUND BUG: Bytes formatting mismatch!")
    print(f"  Input bytes: {test_bytes}")
    print(f"  Expected: {expected_formatted}")
    print(f"  Got: {result}")
    print(f"  Issue: hex() returns lowercase '{actual_hex}' but SQL may expect uppercase")
else:
    print(f"Test passed for bytes formatting")

print("\nAll tests completed.")