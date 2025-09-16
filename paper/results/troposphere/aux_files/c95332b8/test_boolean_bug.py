import troposphere.ram as ram
from hypothesis import given, strategies as st
import pytest


@given(st.floats())
def test_boolean_accepts_floats_unexpectedly(f):
    """The boolean function should not accept float values"""
    # The function is designed for bool, int (0,1), and string conversions
    # But due to using == comparison, it accepts 0.0 and 1.0
    if f == 0.0 or f == 1.0:
        # These floats are accepted but shouldn't be
        result = ram.boolean(f)
        assert isinstance(result, bool)
        assert (f == 0.0 and result == False) or (f == 1.0 and result == True)
    else:
        # Other floats correctly raise ValueError
        with pytest.raises(ValueError):
            ram.boolean(f)