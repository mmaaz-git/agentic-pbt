import troposphere.pipes
from hypothesis import given, strategies as st
import pytest


@given(st.one_of(st.just(float('inf')), st.just(float('-inf'))))
def test_integer_infinity_should_raise_valueerror(x):
    """
    The integer function should raise ValueError for infinity values,
    not OverflowError, and include the specific message format.
    """
    with pytest.raises(ValueError) as excinfo:
        troposphere.pipes.integer(x)
    assert "%r is not a valid integer" % x in str(excinfo.value)