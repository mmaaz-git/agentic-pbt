#!/usr/bin/env python3
"""Reproduction script for shift_lineno bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.utils import shift_lineno

# Test 1: Negative line number bug
def test_func():
    pass

original_code = test_func.__code__

# This will cause ValueError: co_firstlineno must be a positive integer
try:
    # Shifting line 1 by -10 would result in line -9
    shifted_code = shift_lineno(original_code.replace(co_firstlineno=1), -10)
    print("ERROR: Should have raised ValueError")
except ValueError as e:
    print(f"Bug 1 confirmed - Negative line number: {e}")

# Test 2: Integer overflow bug
try:
    # Line number close to max int, adding 200 causes overflow
    large_lineno = 2**31 - 100
    shifted_code = shift_lineno(original_code.replace(co_firstlineno=large_lineno), 200)
    print("ERROR: Should have raised OverflowError")
except OverflowError as e:
    print(f"Bug 2 confirmed - Integer overflow: {e}")