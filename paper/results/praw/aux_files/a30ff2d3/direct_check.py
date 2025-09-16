#!/usr/bin/env python3
"""Direct inspection of praw.const values to find potential bugs."""

import sys
import os

# Add path
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

# Import the module
import praw.const as const

# Create output that can be parsed
print("=== CONST VALUES ===")
print(f"__version__: {repr(const.__version__)}")
print(f"USER_AGENT_FORMAT: {repr(const.USER_AGENT_FORMAT)}")
print(f"MAX_IMAGE_SIZE: {const.MAX_IMAGE_SIZE}")
print(f"MIN_JPEG_SIZE: {const.MIN_JPEG_SIZE}")
print(f"MIN_PNG_SIZE: {const.MIN_PNG_SIZE}")
print(f"JPEG_HEADER: {repr(const.JPEG_HEADER)}")
print(f"PNG_HEADER: {repr(const.PNG_HEADER)}")
print(f"API_PATH type: {type(const.API_PATH)}")
print(f"API_PATH length: {len(const.API_PATH)}")

# Check for potential bugs
print("\n=== POTENTIAL ISSUES ===")

# Bug check 1: Version format
import re
if not re.match(r'^\d+\.\d+\.\d+$', const.__version__):
    print(f"BUG: Version doesn't match semantic versioning: {const.__version__}")

# Bug check 2: Size relationships
if const.MIN_PNG_SIZE >= const.MIN_JPEG_SIZE:
    print(f"BUG: MIN_PNG_SIZE ({const.MIN_PNG_SIZE}) >= MIN_JPEG_SIZE ({const.MIN_JPEG_SIZE})")

if const.MIN_JPEG_SIZE >= const.MAX_IMAGE_SIZE:
    print(f"BUG: MIN_JPEG_SIZE ({const.MIN_JPEG_SIZE}) >= MAX_IMAGE_SIZE ({const.MAX_IMAGE_SIZE})")

if const.MIN_PNG_SIZE >= const.MAX_IMAGE_SIZE:
    print(f"BUG: MIN_PNG_SIZE ({const.MIN_PNG_SIZE}) >= MAX_IMAGE_SIZE ({const.MAX_IMAGE_SIZE})")

# Bug check 3: Header signatures
expected_jpeg = b'\xff\xd8\xff'
if const.JPEG_HEADER != expected_jpeg:
    print(f"BUG: JPEG_HEADER is {repr(const.JPEG_HEADER)}, expected {repr(expected_jpeg)}")

expected_png = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
if const.PNG_HEADER != expected_png:
    print(f"BUG: PNG_HEADER is {repr(const.PNG_HEADER)}, expected {repr(expected_png)}")

# Bug check 4: Format string
try:
    test_result = const.USER_AGENT_FORMAT.format("TestClient")
    if "TestClient" not in test_result:
        print(f"BUG: Format string doesn't include input: {test_result}")
    if const.__version__ not in test_result:
        print(f"BUG: Format string doesn't include version: {test_result}")
except Exception as e:
    print(f"BUG: Format string error: {e}")

print("\n=== CHECK COMPLETE ===")