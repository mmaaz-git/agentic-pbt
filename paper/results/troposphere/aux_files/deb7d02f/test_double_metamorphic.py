import math
import pytest
from hypothesis import given, strategies as st

import troposphere.quicksight as qs


# Test a more interesting metamorphic property
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet="0123456789.-+eE", min_size=1, max_size=20)
))
def test_double_preserves_numeric_value(value):
    """Test that double preserves the numeric value when it succeeds."""
    try:
        result = qs.double(value)
        # The result should be the same as input
        assert result == value
        
        # And both should convert to the same float
        original_float = float(value)
        result_float = float(result)
        
        if not (math.isnan(original_float) and math.isnan(result_float)):
            assert original_float == result_float
    except (ValueError, TypeError):
        # Expected for invalid inputs
        pass


# Test consistency between double and float
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none(),
    st.binary()
))
def test_double_float_consistency(value):
    """Test that double accepts exactly what float accepts."""
    float_accepts = True
    double_accepts = True
    
    try:
        float_result = float(value)
    except (ValueError, TypeError):
        float_accepts = False
    
    try:
        double_result = qs.double(value)
    except (ValueError, TypeError):
        double_accepts = False
    
    # They should behave the same
    assert float_accepts == double_accepts, \
        f"Inconsistency: float({value!r}) {'accepts' if float_accepts else 'rejects'}, " \
        f"double({value!r}) {'accepts' if double_accepts else 'rejects'}"


# Test edge case: very large numbers
@given(st.integers(min_value=10**300, max_value=10**310))
def test_double_large_integers(value):
    """Test double with very large integers."""
    result = qs.double(value)
    assert result == value
    # Should be convertible to float (might be inf)
    float_val = float(result)
    assert math.isinf(float_val) or float_val == float(value)


# Test that boolean validator doesn't accept numeric strings that look like booleans
def test_boolean_numeric_string_edge_cases():
    """Test boolean validator with numeric strings that could be confused with booleans."""
    # "1" is accepted as True, "0" as False
    assert qs.boolean("1") == True
    assert qs.boolean("0") == False
    
    # But what about "1.0" or "0.0"?
    with pytest.raises(ValueError):
        qs.boolean("1.0")
    with pytest.raises(ValueError):
        qs.boolean("0.0")
    
    # What about "01" or "00"?
    with pytest.raises(ValueError):
        qs.boolean("01")
    with pytest.raises(ValueError):
        qs.boolean("00")


# Test with bytes - the validators' behavior with bytes is interesting
def test_validators_with_bytes():
    """Test how validators handle byte strings."""
    # Test boolean with bytes
    with pytest.raises(ValueError):
        qs.boolean(b"true")
    with pytest.raises(ValueError):
        qs.boolean(b"1")
    
    # Test double with bytes
    with pytest.raises(ValueError):
        qs.double(b"3.14")
    with pytest.raises(ValueError):
        qs.double(b"42")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])