exec("""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

mock_connection = Mock(spec=Connection)
cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)

# Test bytes formatting
test_bytes = bytes([0, 1, 2, 255])
result = cursor._format_prepared_param(test_bytes)
print(f'Bytes test result: {result}')

# Check if it's uppercase
hex_part = result[2:-1]  # Remove X' and '
is_uppercase = hex_part == hex_part.upper()
print(f'Hex is uppercase: {is_uppercase}')
print(f'Hex value: {hex_part}')

if not is_uppercase:
    print('BUG FOUND: hex() returns lowercase but format should use uppercase')
""")