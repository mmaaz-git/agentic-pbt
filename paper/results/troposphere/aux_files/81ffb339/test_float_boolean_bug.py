#!/usr/bin/env python3
"""Test for float handling bug in boolean validator."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# The code at line 39 says:
# if x in [True, 1, "1", "true", "True"]:
#     return True
# if x in [False, 0, "0", "false", "False"]:
#     return False

# Let's test what happens with floats
print("Testing float values in boolean validator:")

float_tests = [
    (0.0, "Should this be False?"),
    (1.0, "Should this be True?"),
    (2.0, "What about 2.0?"),
    (0.5, "What about 0.5?"),
    (-1.0, "What about -1.0?"),
    (float('inf'), "What about infinity?"),
    (float('-inf'), "What about negative infinity?"),
]

for value, question in float_tests:
    try:
        result = boolean(value)
        print(f"boolean({value}) = {result} - {question}")
    except ValueError:
        print(f"boolean({value}) raised ValueError - {question}")
    except Exception as e:
        print(f"boolean({value}) raised {type(e).__name__}: {e}")

# Let's understand why this happens
print("\n\nChecking Python equality:")
print(f"1.0 == 1: {1.0 == 1}")
print(f"1.0 in [1]: {1.0 in [1]}")
print(f"0.0 == 0: {0.0 == 0}")
print(f"0.0 in [0]: {0.0 in [0]}")
print(f"2.0 == 1: {2.0 == 1}")
print(f"2.0 in [1]: {2.0 in [1]}")

print("\n\nTesting with Hypothesis:")
from hypothesis import given, strategies as st, settings
import pytest

@given(st.floats())
@settings(max_examples=1000)
def test_float_boolean_behavior(value):
    """Test how boolean validator handles float values."""
    try:
        result = boolean(value)
        # If it doesn't raise, it should only be for 0.0 or 1.0
        assert value in [0.0, 1.0], f"Unexpected success for float {value} -> {result}"
        if value == 1.0:
            assert result is True
        elif value == 0.0:
            assert result is False
    except ValueError:
        # Should raise for all floats except 0.0 and 1.0
        assert value not in [0.0, 1.0], f"Unexpected ValueError for float {value}"

# Run the test
test_float_boolean_behavior()