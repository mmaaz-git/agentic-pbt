#!/usr/bin/env python3
"""Minimal reproduction of boolean validator bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test the bug found by Hypothesis
test_values = [
    0.0,   # Float zero - should raise ValueError but returns False
    1.0,   # Float one - let's see what happens
    -0.0,  # Negative zero
    0.5,   # Other float values
]

print("Testing boolean validator with float values:")
print("-" * 50)

for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({value!r}) = {result!r} (type: {type(value).__name__})")
    except ValueError as e:
        print(f"boolean({value!r}) raised ValueError (expected for non-boolean types)")

print("\n" + "=" * 50)
print("\nExpected behavior according to the code:")
print("The boolean function should only accept:")
print("  - True, 1, '1', 'true', 'True' -> returns True") 
print("  - False, 0, '0', 'false', 'False' -> returns False")
print("  - Everything else -> raises ValueError")

print("\nActual behavior:")
print("  - Float 0.0 is accepted and returns False")
print("  - Float 1.0 is accepted and returns True")
print("\nThis is a bug because floats are not in the documented accepted types.")