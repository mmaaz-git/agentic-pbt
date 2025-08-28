#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from troposphere.validators import integer


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False)
       .filter(lambda x: x != int(x)))
def test_integer_rejects_non_integers(value):
    """
    Property: The integer() validator should reject any float that is not 
    equal to its integer conversion (i.e., has a fractional part).
    """
    try:
        result = integer(value)
        # If we get here without exception, it's a bug
        assert False, f"integer({value}) should raise ValueError but returned {result}"
    except ValueError:
        # This is the expected behavior
        pass


if __name__ == "__main__":
    print("Running property-based test to find integer validator bug...")
    try:
        test_integer_rejects_non_integers()
        print("✓ All tests passed")
    except AssertionError as e:
        print(f"✗ BUG FOUND: {e}")
        print("\nThis confirms that the integer() validator incorrectly accepts")
        print("float values with decimal parts, which violates its intended purpose.")