#!/usr/bin/env python3
"""Focused test for the integer validator infinity bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

# Property: integer validator should handle all numeric inputs gracefully
@given(st.floats())
def test_integer_validator_handles_all_floats(x):
    """
    The integer validator should either:
    1. Successfully validate the input and return it, OR
    2. Raise a ValueError with a descriptive message
    
    It should NEVER raise other exceptions like OverflowError.
    """
    try:
        result = integer(x)
        # If successful, the value should be convertible to int
        int_value = int(x)
    except ValueError as e:
        # This is the expected exception type
        assert "%r is not a valid integer" % x in str(e)
    except OverflowError:
        # This should not happen - it's the bug!
        pytest.fail(f"integer({x}) raised OverflowError instead of ValueError")

if __name__ == "__main__":
    # Run the test
    test_integer_validator_handles_all_floats()