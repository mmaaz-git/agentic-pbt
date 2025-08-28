#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

print("=== Demonstrating integer validator bug ===")
print("The integer() validator is supposed to validate integers.")
print("However, it incorrectly accepts booleans and floats.\n")

# Test cases that should fail but don't
test_cases = [
    (False, bool),
    (True, bool), 
    (0.0, float),
    (1.0, float),
    (3.14, float),
    (-2.5, float)
]

for value, expected_type in test_cases:
    result = integer(value)
    print(f"integer({value!r}) = {result!r} (type: {type(result).__name__})")
    print(f"  ❌ Bug: Returned {expected_type.__name__} instead of raising ValueError")
    print(f"  Expected: Should raise ValueError for non-integer types")
    print()

print("\n=== Why this is a bug ===")
print("The integer validator's purpose is to ensure values are integers.")
print("Accepting booleans and floats violates the principle of type safety.")
print("In Python, isinstance(True, int) returns True because bool is a subclass of int,")
print("but for validation purposes, strict type checking is expected.")
print("\nFloats especially should not pass integer validation as they can have")
print("fractional parts that would be lost in conversion.")