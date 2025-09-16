#!/usr/bin/env python3
"""
Test split_string_literal with negative limit.
"""

import Cython.Compiler.StringEncoding as SE

# Test with negative limit
print("Testing split_string_literal with limit=-1...")
s = "test string"
print(f"Input string: '{s}'")

try:
    result = SE.split_string_literal(s, -1)
    print(f"Result: '{result}'")
    
    # With limit=-1:
    # - Line 305: len(s) < -1 is False for any string
    # - Line 311: end = start + (-1) = start - 1
    # - This means end < start
    # - Line 320: s[start:end] will be empty when end < start
    # - Line 321: start = end, so start decreases
    # This will also cause issues!
    
except Exception as e:
    print(f"Exception: {e}")