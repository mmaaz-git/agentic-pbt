"""Minimal reproduction of the boolean validator bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test the bug
test_values = [0.0, 1.0, 0.5, -1.0, 2.0]

for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({value}) = {result} (type: {type(result).__name__})")
    except ValueError as e:
        print(f"boolean({value}) raised ValueError: {e}")

# The issue: 0.0 == 0 and 1.0 == 1 in Python's comparison
print(f"\nComparison check:")
print(f"0.0 == 0: {0.0 == 0}")
print(f"1.0 == 1: {1.0 == 1}")
print(f"0.0 in [0]: {0.0 in [0]}")
print(f"1.0 in [1]: {1.0 in [1]}")