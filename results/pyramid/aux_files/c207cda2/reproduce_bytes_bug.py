#!/usr/bin/env python3
"""Reproduce the bytes_ encoding bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.util import bytes_

# This should fail with UnicodeEncodeError
text = 'Ā'  # Character with codepoint 256 (outside latin-1 range)
print(f"Attempting to convert: {text!r} (codepoint: {ord(text[0])})")

try:
    result = bytes_(text)
    print(f"Success: {result!r}")
except UnicodeEncodeError as e:
    print(f"Error: {e}")
    print(f"The bytes_ function fails on Unicode characters outside the Latin-1 range.")
    print(f"This is problematic because the function doesn't document this limitation.")

# Check the docstring
print(f"\nbytes_ docstring: {bytes_.__doc__}")

# Test with valid latin-1 character
text2 = 'ÿ'  # Character with codepoint 255 (max latin-1)
print(f"\nTesting with {text2!r} (codepoint: {ord(text2[0])})")
result2 = bytes_(text2)
print(f"Success: {result2!r}")