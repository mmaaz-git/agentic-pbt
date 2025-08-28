#!/usr/bin/env python3
"""Minimal reproduction of boolean validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test case that should fail but doesn't
test_value = 0.0
print(f"Testing boolean({test_value})")
try:
    result = boolean(test_value)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    print("BUG: boolean(0.0) should raise ValueError but returns False")
except ValueError:
    print("Correctly raised ValueError")

# Similar test with 1.0
test_value = 1.0
print(f"\nTesting boolean({test_value})")
try:
    result = boolean(test_value)
    print(f"Result: {result}") 
    print(f"Type: {type(result)}")
    print("BUG: boolean(1.0) should raise ValueError but returns True")
except ValueError:
    print("Correctly raised ValueError")