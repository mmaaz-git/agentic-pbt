"""Property-based tests for troposphere.s3tables.integer function."""

import math
from hypothesis import given, strategies as st
import troposphere.s3tables as s3t


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_property(x):
    """
    Property: The integer validator should only accept values that represent
    whole numbers (integers), and reject values with fractional parts.
    
    Based on the function name and docstring, it validates "integers".
    """
    is_whole_number = x == math.floor(x)  # True if x is a whole number
    
    try:
        result = s3t.integer(x)
        # If it succeeds, the value should be a whole number
        assert is_whole_number, f"integer() accepted {x} which has fractional part {x - math.floor(x)}"
        # And it should return the original value unchanged
        assert result == x
    except ValueError:
        # If it raises ValueError, the value should NOT be a whole number
        assert not is_whole_number, f"integer() rejected {x} which is a whole number"


@given(st.integers())
def test_integer_accepts_all_integers(n):
    """
    Property: The integer validator should accept all integer values
    and return them unchanged.
    """
    result = s3t.integer(n)
    assert result == n
    assert type(result) == int


@given(st.text(alphabet=st.characters(blacklist_categories=('Nd',)), min_size=1))
def test_integer_rejects_non_numeric_strings(s):
    """
    Property: The integer validator should reject strings that cannot
    be converted to integers.
    """
    # This generates strings without digits, so they can't be valid integers
    try:
        s3t.integer(s)
        assert False, f"integer() should have rejected non-numeric string {repr(s)}"
    except ValueError as e:
        assert s in str(e), "Error message should mention the invalid input"
        assert "not a valid integer" in str(e)


@given(st.one_of(st.none(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers())))
def test_integer_rejects_non_numeric_types(value):
    """
    Property: The integer validator should reject non-numeric types
    like None, lists, and dictionaries.
    """
    try:
        s3t.integer(value)
        assert False, f"integer() should have rejected {type(value).__name__}: {repr(value)}"
    except (ValueError, TypeError) as e:
        assert "not a valid integer" in str(e)