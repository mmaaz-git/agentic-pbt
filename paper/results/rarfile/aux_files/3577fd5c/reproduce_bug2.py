#!/usr/bin/env python3
"""Minimal reproduction of to_datetime sanitization bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/rarfile_env/lib/python3.13/site-packages')
import rarfile

# Bug: to_datetime doesn't properly sanitize negative seconds
time_tuple = (2020, 1, 1, 0, 0, -1)
print(f"Input tuple: {time_tuple}")

try:
    result = rarfile.to_datetime(time_tuple)
    print(f"Result: {result}")
except ValueError as e:
    print(f"BUG: ValueError raised instead of sanitizing: {e}")
    print("Expected: Function should sanitize invalid values according to its documentation")