#!/usr/bin/env python3
"""Minimal reproduction of positive_integer bug."""

import troposphere.validators as validators

# Bug: positive_integer accepts negative floats that round to 0
test_value = -0.5
result = validators.positive_integer(test_value)
print(f"positive_integer({test_value}) = {result}")
print(f"int(result) = {int(result)}")

# This should raise ValueError but doesn't
assert result == -0.5  # The original negative value is returned!
assert int(result) == 0  # But int() of it is 0

print("\nBUG: positive_integer accepts -0.5 even though it's negative!")
print("The function returns the original negative value -0.5")
print("This violates the contract that positive_integer should only accept non-negative values")