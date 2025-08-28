#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.limits import safe_string

try:
    result = safe_string(b'\x80')
    print(f"Result: {result}")
except UnicodeDecodeError as e:
    print(f"UnicodeDecodeError: {e}")
    print("Bug confirmed: safe_string() crashes on non-UTF8 bytes")