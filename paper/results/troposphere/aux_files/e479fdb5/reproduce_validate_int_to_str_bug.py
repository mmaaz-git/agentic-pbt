#!/usr/bin/env python3
"""Minimal reproduction of validate_int_to_str bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.autoscaling import validate_int_to_str

# Test cases that should work
print("Testing valid inputs:")
print(f"validate_int_to_str(5) = {validate_int_to_str(5)}")
print(f"validate_int_to_str('5') = {validate_int_to_str('5')}")

# This should raise TypeError but instead raises ValueError
print("\nTesting invalid string input:")
try:
    result = validate_int_to_str(':')
    print(f"validate_int_to_str(':') = {result}")
except TypeError as e:
    print(f"Correctly raised TypeError: {e}")
except ValueError as e:
    print(f"BUG: Raised ValueError instead of TypeError: {e}")