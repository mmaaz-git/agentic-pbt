#!/usr/bin/env python3
"""Minimal reproduction of integer validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Test integer validator with float input
test_cases = [
    0.0,
    1.0,
    -1.0, 
    3.14,
    100.5,
]

print("Testing integer validator with float inputs:")
for value in test_cases:
    try:
        result = integer(value)
        print(f"  integer({value}) = {result} (type: {type(result).__name__})")
        
        # Check if it's actually an integer
        if not isinstance(result, int):
            print(f"    ❌ BUG: Expected int, got {type(result).__name__}")
        else:
            print(f"    ✓ Correctly returned int")
    except Exception as e:
        print(f"  integer({value}) raised {e}")