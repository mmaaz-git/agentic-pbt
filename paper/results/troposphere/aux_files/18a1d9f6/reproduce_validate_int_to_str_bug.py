#!/usr/bin/env python3
"""Minimal reproduction of validate_int_to_str Unicode digit bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.cloudformation import validate_int_to_str

# Unicode superscript 2 is considered a digit by Python's isdigit()
unicode_digit = '²'
print(f"Testing with: '{unicode_digit}'")
print(f"unicode_digit.isdigit() = {unicode_digit.isdigit()}")

try:
    result = validate_int_to_str(unicode_digit)
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError: {e}")
    print("BUG: validate_int_to_str crashes on Unicode digit characters that pass isdigit() but fail int()")