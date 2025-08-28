#!/usr/bin/env python3
import sys
sys.path.append('/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

import storage3

# Test case 1: Non-ASCII character in header key
try:
    client = storage3.create_client(
        url="http://localhost:8000",
        headers={'\x80': ''},
        is_async=False
    )
    print("Test 1 passed - should have failed!")
except UnicodeEncodeError as e:
    print(f"Test 1: UnicodeEncodeError as expected - {e}")

# Test case 2: Non-ASCII character in header value
try:
    client = storage3.create_client(
        url="http://localhost:8000",
        headers={'test': '\x80'},
        is_async=False
    )
    print("Test 2 passed - should have failed!")
except UnicodeEncodeError as e:
    print(f"Test 2: UnicodeEncodeError as expected - {e}")

# Test case 3: Valid ASCII headers should work
try:
    client = storage3.create_client(
        url="http://localhost:8000",
        headers={'Authorization': 'Bearer token123'},
        is_async=False
    )
    print("Test 3: Successfully created client with valid headers")
except Exception as e:
    print(f"Test 3 failed unexpectedly: {e}")

print("\nBug confirmed: storage3.create_client() crashes with non-ASCII characters in headers")