#!/usr/bin/env python3
"""Explore pyramid.csrf behavior to find potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.util import SimpleSerializer, is_same_domain, strings_differ, bytes_
import string

print("Testing pyramid.csrf components...")
print("=" * 60)

# Test 1: SimpleSerializer edge cases
print("\n1. Testing SimpleSerializer with edge cases:")
serializer = SimpleSerializer()

test_cases = [
    "",  # Empty string
    "hello",  # Normal text
    "hello\x00world",  # Null byte
    "🦄",  # Unicode emoji
    "a" * 10000,  # Long string
    "\n\r\t",  # Whitespace
]

for test in test_cases:
    try:
        serialized = serializer.dumps(test)
        deserialized = serializer.loads(serialized)
        if deserialized != test:
            print(f"  ✗ FAILURE: Round-trip failed for {repr(test)[:50]}")
            print(f"    Expected: {repr(test)[:50]}")
            print(f"    Got: {repr(deserialized)[:50]}")
        else:
            print(f"  ✓ OK: {repr(test)[:30]}")
    except Exception as e:
        print(f"  ✗ ERROR: {repr(test)[:30]} - {e}")

# Test 2: is_same_domain edge cases
print("\n2. Testing is_same_domain edge cases:")

domain_tests = [
    # (host, pattern, expected)
    ("example.com", ".example.com", True),
    ("sub.example.com", ".example.com", True),
    ("example.com", ".", True),  # Pattern is just "."
    ("", ".", False),  # Empty host
    ("example.com", ".com", True),  # TLD wildcard
    ("example.com", "..example.com", False),  # Double dot
    ("example.com", ".example.com.", False),  # Trailing dot in pattern
    ("example.com.", ".example.com", False),  # Trailing dot in host
    ("EXAMPLE.COM", "example.com", True),  # Case insensitive
]

for host, pattern, expected in domain_tests:
    result = is_same_domain(host, pattern)
    if result != expected:
        print(f"  ✗ FAILURE: is_same_domain({repr(host)}, {repr(pattern)})")
        print(f"    Expected: {expected}, Got: {result}")
    else:
        print(f"  ✓ OK: is_same_domain({repr(host)}, {repr(pattern)}) = {result}")

# Test 3: strings_differ edge cases
print("\n3. Testing strings_differ edge cases:")

string_tests = [
    # (s1, s2, expected_differ)
    (b"", b"", False),  # Empty strings
    (b"a", b"a", False),  # Same single char
    (b"a", b"b", True),  # Different single char
    (b"abc", b"ab", True),  # Different lengths
    (b"\x00", b"\x00", False),  # Null bytes
    (b"a" * 1000, b"a" * 1000, False),  # Long identical
    (b"a" * 1000, b"a" * 999 + b"b", True),  # Long with difference at end
]

for s1, s2, expected in string_tests:
    result = strings_differ(s1, s2)
    if result != expected:
        print(f"  ✗ FAILURE: strings_differ({repr(s1)[:30]}, {repr(s2)[:30]})")
        print(f"    Expected: {expected}, Got: {result}")
    else:
        print(f"  ✓ OK: strings_differ({repr(s1)[:30]}, {repr(s2)[:30]}) = {result}")

# Test 4: Token generation
print("\n4. Testing token generation:")
from pyramid.csrf import SessionCSRFStoragePolicy

policy = SessionCSRFStoragePolicy()
tokens = []
for i in range(10):
    token = policy._token_factory()
    tokens.append(token)
    
    # Check format
    if len(token) != 32:
        print(f"  ✗ Token {i} has wrong length: {len(token)} (expected 32)")
    elif not all(c in string.hexdigits for c in token):
        print(f"  ✗ Token {i} has non-hex characters: {token}")
    else:
        print(f"  ✓ Token {i}: {token[:8]}... (valid)")

# Check uniqueness
if len(set(tokens)) != len(tokens):
    print(f"  ✗ FAILURE: Duplicate tokens generated!")
else:
    print(f"  ✓ All {len(tokens)} tokens are unique")

print("\n" + "=" * 60)
print("Exploration complete!")