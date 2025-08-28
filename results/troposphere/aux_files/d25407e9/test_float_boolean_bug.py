#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean
from hypothesis import given, strategies as st
import math

print("=== Investigation: Boolean validator accepts floats 1.0 and 0.0 ===")
print("This happens because Python's equality check 1.0 == 1 returns True")
print()

# Demonstration
print("Code check: if x in [True, 1, '1', 'true', 'True']:")
print(f"  1.0 in [True, 1, '1', 'true', 'True'] = {1.0 in [True, 1, '1', 'true', 'True']}")
print(f"  0.0 in [False, 0, '0', 'false', 'False'] = {0.0 in [False, 0, '0', 'false', 'False']}")
print()

# Test various float values
float_tests = [
    1.0,
    0.0,
    1.00000000000001,  # Very close to 1
    0.99999999999999,  # Very close to 1
    -0.0,  # Negative zero
    2.0,
    -1.0,
]

print("Testing float values:")
for val in float_tests:
    try:
        result = boolean(val)
        print(f"  boolean({val}) = {result}")
    except ValueError:
        print(f"  boolean({val}) raised ValueError")

print("\n=== Property Test: Floats equal to integers ===")

# Hypothesis test to find more edge cases
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_boolean_acceptance(x):
    """Test which floats are accepted by boolean validator"""
    try:
        result = boolean(x)
        # If it succeeds, x must be equal to 0, 1, True, or False
        assert x in [0.0, 1.0, 0, 1, True, False], f"Unexpected success: boolean({x}) = {result}"
        # And the result should match what we expect
        if x in [1.0, 1, True]:
            assert result is True
        elif x in [0.0, 0, False]:
            assert result is False
    except ValueError:
        # Should fail for anything not equal to 0 or 1
        assert x not in [0.0, 1.0, 0, 1, True, False], f"Unexpected failure for {x}"

print("Running property test...")
try:
    test_float_boolean_acceptance()
    print("Property test passed!")
except AssertionError as e:
    print(f"Property test failed: {e}")

print("\n=== Testing special float edge cases ===")
special_floats = [
    float('nan'),
    float('inf'),
    float('-inf'),
]

for val in special_floats:
    try:
        result = boolean(val)
        print(f"  boolean({val}) = {result} - UNEXPECTED SUCCESS")
    except ValueError:
        print(f"  boolean({val}) raised ValueError - as expected")

print("\n=== Documentation vs Implementation Discrepancy ===")
print("The boolean function's type hints suggest it only accepts specific literals,")
print("but the implementation uses 'in' operator which allows float equivalents.")
print()
print("Type hints say:")
print("  @overload")
print("  def boolean(x: Literal[True, 1, 'true', 'True']) -> Literal[True]: ...")
print()
print("But implementation accepts:")
print("  - Floats 1.0 and 0.0 due to Python's equality semantics")
print("  - This could be considered a bug or undocumented behavior")