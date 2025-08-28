#!/usr/bin/env python3
"""Simple direct tests for praw.const properties."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

import praw.const as const

print("Testing praw.const module...")
print(f"__version__ = {const.__version__}")
print(f"USER_AGENT_FORMAT = {const.USER_AGENT_FORMAT}")
print(f"MAX_IMAGE_SIZE = {const.MAX_IMAGE_SIZE}")
print(f"MIN_JPEG_SIZE = {const.MIN_JPEG_SIZE}")
print(f"MIN_PNG_SIZE = {const.MIN_PNG_SIZE}")
print(f"JPEG_HEADER = {const.JPEG_HEADER}")
print(f"PNG_HEADER = {const.PNG_HEADER}")

# Test 1: Check header values
print("\n=== Test 1: Image Headers ===")
assert const.JPEG_HEADER == b'\xff\xd8\xff', f"JPEG header mismatch: {const.JPEG_HEADER}"
print("✓ JPEG header is correct")

assert const.PNG_HEADER == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', f"PNG header mismatch: {const.PNG_HEADER}"
print("✓ PNG header is correct")

# Test 2: Size relationships
print("\n=== Test 2: Size Constants ===")
print(f"MIN_PNG_SIZE ({const.MIN_PNG_SIZE}) < MIN_JPEG_SIZE ({const.MIN_JPEG_SIZE}): {const.MIN_PNG_SIZE < const.MIN_JPEG_SIZE}")
print(f"MIN_JPEG_SIZE ({const.MIN_JPEG_SIZE}) < MAX_IMAGE_SIZE ({const.MAX_IMAGE_SIZE}): {const.MIN_JPEG_SIZE < const.MAX_IMAGE_SIZE}")

# Test 3: Format string
print("\n=== Test 3: User Agent Format ===")
test_name = "TestClient"
formatted = const.USER_AGENT_FORMAT.format(test_name)
print(f"Format test: '{test_name}' -> '{formatted}'")
expected = f"{test_name} PRAW/{const.__version__}"
assert formatted == expected, f"Format mismatch: expected '{expected}', got '{formatted}'"
print("✓ Format string works correctly")

print("\n=== All basic tests passed ===")