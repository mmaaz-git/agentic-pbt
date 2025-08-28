#!/usr/bin/env python3
"""Reproduce the integer validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Test the failing case
test_value = 0.5
print(f"Testing integer({test_value})")

try:
    result = integer(test_value)
    print(f"Result: {result}")
    print(f"Result type: {type(result)}")
    print(f"int(result): {int(result)}")
    print("BUG: integer() accepted a non-integer float value!")
except ValueError as e:
    print(f"Correctly rejected with: {e}")

# Test a few more cases
test_cases = [0.5, 1.5, 2.7, -3.14, 100.001]

for val in test_cases:
    try:
        result = integer(val)
        print(f"integer({val}) = {result} (type: {type(result).__name__})")
    except ValueError as e:
        print(f"integer({val}) raised ValueError: {e}")