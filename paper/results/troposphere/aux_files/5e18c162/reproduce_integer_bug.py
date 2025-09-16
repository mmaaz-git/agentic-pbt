#!/usr/bin/env python3
"""
Minimal reproduction of the integer validator bug in troposphere.
The integer validator accepts float values when it should reject them.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# The integer validator is supposed to validate that a value is an integer
# But it accepts floats without raising an error

print("Testing integer validator with float values:")
print("=" * 50)

test_floats = [0.5, 1.7, -2.3, 100.99]

for value in test_floats:
    try:
        result = integer(value)
        print(f"BUG: integer({value}) returned {result} (type: {type(result).__name__})")
        print(f"     Expected: ValueError should be raised")
        print(f"     Actual: Returned the float value unchanged")
        print()
    except ValueError as e:
        print(f"OK: integer({value}) raised ValueError: {e}")
        print()

print("\nTesting with actual integers (should work):")
print("=" * 50)

test_ints = [0, 1, -5, 100]
for value in test_ints:
    try:
        result = integer(value)
        print(f"OK: integer({value}) = {result}")
    except ValueError as e:
        print(f"ERROR: integer({value}) raised unexpected error: {e}")

print("\n" + "=" * 50)
print("CONCLUSION: The integer validator has a bug where it accepts float values")
print("instead of rejecting them. This violates the expected behavior of an ")
print("integer validator which should only accept integer values.")