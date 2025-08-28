#!/usr/bin/env python3
"""Test STS module properties."""

import sys
import json
import urllib.parse

sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

print("Testing STS module properties...")

# Test 1: Options encoding/decoding
print("\n1. Testing options encoding/decoding:")
test_options = [
    {"key": "value"},
    {"unicode": "你好世界"},
    {"special": "!@#$%^&*()"},
    {"nested": {"inner": "value"}},
    {"number": 123},
    {"bool": True},
    {"null": None},
]

for options in test_options:
    print(f"\nOriginal options: {options}")
    
    # Encode like the STS client does
    encoded = urllib.parse.quote(json.dumps(options))
    print(f"Encoded: {encoded}")
    
    # Decode back
    decoded_json = urllib.parse.unquote(encoded)
    decoded_options = json.loads(decoded_json)
    print(f"Decoded: {decoded_options}")
    print(f"Match: {decoded_options == options}")

# Test 2: Empty field removal
print("\n\n2. Testing empty field removal:")

test_bodies = [
    {
        "grant_type": "authorization_code",
        "resource": None,
        "audience": "",
        "scope": "",
        "requested_token_type": None,
    },
    {
        "grant_type": "refresh_token",
        "resource": "https://example.com",
        "audience": None,
        "scope": "read write",
        "requested_token_type": "",
    },
]

for original_body in test_bodies:
    print(f"\nOriginal body: {original_body}")
    
    # Remove empty fields like the code does
    cleaned_body = dict(original_body)
    for k, v in dict(cleaned_body).items():
        if v is None or v == "":
            del cleaned_body[k]
    
    print(f"After removal: {cleaned_body}")
    
    # Check no empty values remain
    has_empty = any(v is None or v == "" for v in cleaned_body.values())
    print(f"Has empty values: {has_empty}")

# Test 3: URL encoding with special characters
print("\n\n3. Testing URL encoding with special characters:")

special_strings = [
    "hello world",
    "key=value&other=data",
    "https://example.com/path?query=1",
    "你好世界",
    "emoji: 🚀",
    '{"json": "value"}',
]

for text in special_strings:
    print(f"\nOriginal: {text}")
    encoded = urllib.parse.quote(text)
    print(f"Encoded: {encoded}")
    decoded = urllib.parse.unquote(encoded)
    print(f"Decoded: {decoded}")
    print(f"Match: {decoded == text}")