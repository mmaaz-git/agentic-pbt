#!/usr/bin/env python3
"""Minimal reproduction of the write() return value bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/base64io_env/lib/python3.13/site-packages')

import io
import base64io

# Test case 1: Single byte write
print("Test 1: Writing single byte")
buffer = io.BytesIO()
with base64io.Base64IO(buffer) as b64:
    data = b'\x00'
    bytes_written = b64.write(data)
    print(f"  Data: {data!r} (length: {len(data)})")
    print(f"  write() returned: {bytes_written}")
    print(f"  Expected return: {len(data)}")
    print(f"  BUG: Returns {bytes_written} instead of {len(data)}")

print("\nTest 2: Writing 2 bytes")
buffer = io.BytesIO()
with base64io.Base64IO(buffer) as b64:
    data = b'AB'
    bytes_written = b64.write(data)
    print(f"  Data: {data!r} (length: {len(data)})")
    print(f"  write() returned: {bytes_written}")
    print(f"  Expected return: {len(data)}")
    if bytes_written != len(data):
        print(f"  BUG: Returns {bytes_written} instead of {len(data)}")

print("\nTest 3: Writing 3 bytes (complete base64 chunk)")
buffer = io.BytesIO()
with base64io.Base64IO(buffer) as b64:
    data = b'ABC'
    bytes_written = b64.write(data)
    print(f"  Data: {data!r} (length: {len(data)})")
    print(f"  write() returned: {bytes_written}")
    print(f"  Expected return: {len(data)}")
    print(f"  Result: {'OK' if bytes_written == len(data) else 'BUG'}")

print("\nTest 4: Writing 4 bytes")
buffer = io.BytesIO()
with base64io.Base64IO(buffer) as b64:
    data = b'ABCD'
    bytes_written = b64.write(data)
    print(f"  Data: {data!r} (length: {len(data)})")
    print(f"  write() returned: {bytes_written}")
    print(f"  Expected return: {len(data)}")
    if bytes_written != len(data):
        print(f"  BUG: Returns {bytes_written} instead of {len(data)}")

print("\nAnalysis:")
print("The bug occurs when data length is not divisible by 3.")
print("The write() method returns the number of ENCODED bytes written")
print("to the underlying stream, not the number of USER bytes written.")
print("\nLooking at the code (lines 207-213):")
print("- When len(data) % 3 == 0: returns wrapped.write(encoded)")
print("- When len(data) % 3 != 0: buffers some bytes, returns wrapped.write(partial_encoded)")
print("\nThe return value is from the wrapped stream's write(), which is")
print("the number of base64-encoded bytes, not the original byte count.")