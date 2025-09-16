import sys
import os
import re
import json
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.auth import (
    BasicAuthentication,
    JWTAuthentication,
    _OAuth2TokenBearer,
)

# Test 1: Simple equality test with BasicAuthentication
print("Test 1: BasicAuthentication equality")
auth1 = BasicAuthentication("user1", "pass1")
auth2 = BasicAuthentication("user1", "pass1")
auth3 = BasicAuthentication("user2", "pass2")

assert auth1 == auth1, "Reflexive equality failed"
assert auth1 == auth2, "Same values should be equal"
assert auth1 != auth3, "Different values should not be equal"
print("✓ BasicAuthentication equality tests passed")

# Test 2: JWT equality
print("\nTest 2: JWTAuthentication equality")
jwt1 = JWTAuthentication("token123")
jwt2 = JWTAuthentication("token123")
jwt3 = JWTAuthentication("token456")

assert jwt1 == jwt1, "Reflexive equality failed"
assert jwt1 == jwt2, "Same tokens should be equal"
assert jwt1 != jwt3, "Different tokens should not be equal"
print("✓ JWTAuthentication equality tests passed")

# Test 3: Authentication header parsing
print("\nTest 3: Authentication header parsing")
header1 = 'key1=value1, key2="value with spaces", KEY3=VALUE3'
parsed = _OAuth2TokenBearer._parse_authenticate_header(header1)
print(f"  Input header: {header1}")
print(f"  Parsed result: {parsed}")

# Check if keys are lowercased
assert 'key1' in parsed, "key1 should be in parsed result"
assert 'key2' in parsed, "key2 should be in parsed result"
assert 'key3' in parsed, "key3 should be in parsed result (lowercased)"
assert parsed['key1'] == 'value1', f"Expected 'value1', got '{parsed['key1']}'"
assert parsed['key2'] == 'value with spaces', f"Expected 'value with spaces', got '{parsed['key2']}'"
assert parsed['key3'] == 'VALUE3', f"Expected 'VALUE3', got '{parsed['key3']}'"
print("✓ Authentication header parsing tests passed")

# Test 4: Edge case - header with equals sign in value
print("\nTest 4: Header parsing with equals in value")
header2 = 'key="value=with=equals"'
parsed2 = _OAuth2TokenBearer._parse_authenticate_header(header2)
print(f"  Input header: {header2}")
print(f"  Parsed result: {parsed2}")
assert parsed2['key'] == 'value=with=equals', f"Expected 'value=with=equals', got '{parsed2['key']}'"
print("✓ Header with equals in value parsed correctly")

# Test 5: Cache key construction
print("\nTest 5: Cache key construction")
key1 = _OAuth2TokenBearer._construct_cache_key("host1", "user1")
key2 = _OAuth2TokenBearer._construct_cache_key("host1", None)
key3 = _OAuth2TokenBearer._construct_cache_key(None, "user1")

print(f"  Key with host and user: {key1}")
print(f"  Key with host only: {key2}")
print(f"  Key with None host and user: {key3}")

assert key1 == "host1@user1", f"Expected 'host1@user1', got '{key1}'"
assert key2 == "host1", f"Expected 'host1', got '{key2}'"
assert key3 == "None@user1", f"Expected 'None@user1', got '{key3}'"
print("✓ Cache key construction tests passed")

# Test 6: Bearer prefix case-insensitive matching
print("\nTest 6: Bearer prefix case-insensitive matching")
pattern = _OAuth2TokenBearer._BEARER_PREFIX
test_cases = ['bearer token', 'Bearer token', 'BEARER token', 'BeArEr token']
for test_str in test_cases:
    match = pattern.search(test_str)
    assert match is not None, f"Pattern should match '{test_str}'"
    print(f"  ✓ Matched: {test_str}")
print("✓ Bearer prefix matching tests passed")

print("\n" + "="*50)
print("All tests passed successfully!")