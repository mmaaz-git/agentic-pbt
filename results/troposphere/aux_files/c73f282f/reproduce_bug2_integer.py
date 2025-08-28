#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Reproduce integer validator bug with non-integer float values"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Bug: integer validator accepts non-integer float values
# These should raise ValueError but don't

print("Testing integer validator with non-integer float values:")

# Test case 1: 0.5 should not be accepted as an integer
try:
    result = integer(0.5)
    print(f"integer(0.5) = {result}")
    print("BUG: Non-integer float 0.5 was accepted as an integer!")
    # Verify it's not actually an integer
    print(f"  int(0.5) = {int(0.5)} (loses precision!)")
except ValueError as e:
    print(f"0.5 correctly rejected: {e}")

# Test case 2: 3.14 should not be accepted as an integer
try:
    result = integer(3.14)
    print(f"integer(3.14) = {result}")
    print("BUG: Non-integer float 3.14 was accepted as an integer!")
    print(f"  int(3.14) = {int(3.14)} (loses precision!)")
except ValueError as e:
    print(f"3.14 correctly rejected: {e}")

# Test case 3: -2.7 should not be accepted as an integer
try:
    result = integer(-2.7)
    print(f"integer(-2.7) = {result}")
    print("BUG: Non-integer float -2.7 was accepted as an integer!")
    print(f"  int(-2.7) = {int(-2.7)} (loses precision!)")
except ValueError as e:
    print(f"-2.7 correctly rejected: {e}")

# Show that integer floats ARE accepted (which might be intended)
print("\nNote: Integer-valued floats are accepted:")
try:
    result = integer(5.0)
    print(f"integer(5.0) = {result} (this might be intentional)")
except ValueError as e:
    print(f"5.0 rejected: {e}")

print("\nThe issue: The integer validator only checks if int(x) succeeds,")
print("but int() can convert floats, truncating decimal parts.")
print("This allows non-integer floats to pass validation, losing precision silently.")