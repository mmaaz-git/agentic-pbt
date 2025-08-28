#!/usr/bin/env python3
"""Minimal reproduction of sanitize_filename idempotence bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/rarfile_env/lib/python3.13/site-packages')
import rarfile

# Bug: sanitize_filename is not idempotent on Windows paths
filename = '0/0'
is_win32 = True
pathsep = "\\"

# First application
result1 = rarfile.sanitize_filename(filename, pathsep, is_win32)
print(f"First application: '{filename}' -> '{result1}'")

# Second application  
result2 = rarfile.sanitize_filename(result1, pathsep, is_win32)
print(f"Second application: '{result1}' -> '{result2}'")

# Check idempotence
if result1 != result2:
    print(f"BUG: Not idempotent! '{result1}' != '{result2}'")
else:
    print("OK: Function is idempotent")