#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

print("=== Confirming Bug: integer() accepts floats with decimal parts ===\n")

# According to the integer validator code:
# It calls int(x) to check if conversion is possible
# But then returns the original x, not the converted value
# This means floats like 10.5 pass validation

test_cases = [
    10.5,
    3.14,
    -2.7,
    999.999,
    0.1,
]

print("Testing integer() with float values that have decimal parts:")
for val in test_cases:
    try:
        result = integer(val)
        print(f"  ✗ BUG CONFIRMED: integer({val}) = {result}")
        print(f"    Expected: ValueError ('{val} is not a valid integer')")
        print(f"    Actual: Returned {result} without error")
        print(f"    Note: int({val}) = {int(val)}, which succeeds but loses precision")
        print()
    except ValueError as e:
        print(f"  ✓ integer({val}) correctly raised ValueError: {e}")
        print()

print("Root cause analysis:")
print("  The integer() function in validators/__init__.py does:")
print("    1. Try int(x) to see if conversion is possible")
print("    2. If no exception, return the original x")
print("  Problem: int(10.5) succeeds (returns 10), so 10.5 passes validation")
print("  This violates the expected behavior that only valid integers should pass")

print("\nReproducing with a simple example:")
print("  >>> from troposphere.validators import integer")
print("  >>> integer(10.5)")
print(f"  {integer(10.5)}")

print("\nThis is a genuine bug because:")
print("  1. The function is named 'integer' and should only accept integer values")
print("  2. The docstring/purpose is to validate integers")
print("  3. Accepting 10.5 as a valid integer is incorrect")
print("  4. This could lead to unexpected behavior in AWS CloudFormation templates")