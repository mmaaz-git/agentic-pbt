#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal

print("=== BUG 1: Invalid percent encoding accepted ===")
print("\nThe traversal_path function should raise URLDecodeError for invalid")
print("percent-encoded sequences, but instead accepts them as-is.\n")

# Test cases with invalid percent encoding
invalid_encodings = ['%', '%%', '%G', '%ZZ', '%1', '%%%', '%Q', 'foo%', 'foo%1bar']

for encoding in invalid_encodings:
    path = '/' + encoding
    try:
        result = traversal.traversal_path(path)
        print(f"✗ ACCEPTED (BUG): traversal_path('{path}') = {result}")
    except traversal.URLDecodeError as e:
        print(f"✓ REJECTED (correct): traversal_path('{path}') raised URLDecodeError")

print("\n=== BUG 2: Null bytes preserved in path segments ===")
print("\nThe split_path_info function preserves null bytes in path segments,")
print("which could be a security vulnerability.\n")

# Test cases with null bytes
null_byte_paths = [
    '/foo\x00bar',
    '/\x00',
    '/test\x00/path',
    '/safe/../\x00/etc/passwd'
]

for path in null_byte_paths:
    result = traversal.split_path_info(path)
    print(f"split_path_info({path!r}) = {result!r}")
    
    # Check if null bytes are preserved
    for segment in result:
        if '\x00' in segment:
            print(f"  ✗ NULL BYTE PRESERVED (BUG): {segment!r}")

print("\n=== Comparison with standard URL decoding ===")
print("\nStandard urllib.parse.unquote correctly rejects invalid encodings:\n")

import urllib.parse

for encoding in ['%', '%%', '%G', '%ZZ']:
    path = '/' + encoding
    try:
        # urllib doesn't reject invalid encodings, it passes them through
        decoded = urllib.parse.unquote(path)
        print(f"urllib.parse.unquote('{path}') = '{decoded}'")
    except Exception as e:
        print(f"urllib.parse.unquote('{path}') raised {type(e).__name__}")

print("\n=== Security implications ===")
print("\n1. Invalid percent encoding could bypass security filters")
print("2. Null bytes could enable path traversal attacks")
print("3. Inconsistent behavior between traversal_path and standard URL decoding")