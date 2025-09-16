import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.validators import boolean, double

# Test 1: Boolean idempotence property
@given(st.one_of(
    st.sampled_from([True, False, 0, 1, "0", "1", "true", "false", "True", "False"])
))
def test_boolean_idempotence(value):
    """Test that boolean function is idempotent for valid inputs"""
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result2 == result1

# Test 2: Boolean contract property - valid True values
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_returns_true(value):
    """Test that specified values return True as documented"""
    assert boolean(value) is True

# Test 3: Boolean contract property - valid False values  
@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_returns_false(value):
    """Test that specified values return False as documented"""
    assert boolean(value) is False

# Test 4: Boolean contract property - invalid values raise ValueError
@given(st.one_of(
    st.text().filter(lambda x: x not in ["0", "1", "true", "false", "True", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_raises_on_invalid(value):
    """Test that invalid values raise ValueError as documented"""
    with pytest.raises(ValueError):
        boolean(value)

# Test 5: Double type preservation property
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet="0123456789.-+eE", min_size=1).filter(lambda x: x not in ["-", "+", ".", "e", "E", "-.", "+."])
))
def test_double_type_preservation(value):
    """Test that double preserves the original type/value when valid"""
    try:
        float(value)
        result = double(value)
        assert result == value
        assert result is value
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            double(value)

# Test 6: Double validation property - accepts float-convertible values
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.sampled_from(["1", "1.0", "-1", "1e5", "1.5e-3", "0", "-0"])
))
def test_double_accepts_valid(value):
    """Test that double accepts values convertible to float"""
    result = double(value) 
    assert result == value
    float(result)  # Should not raise

# Test 7: Double validation property - rejects non-float-convertible values
@given(st.one_of(
    st.text(min_size=1).filter(lambda x: not all(c in "0123456789.-+eE " for c in x)),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.booleans()
))
def test_double_rejects_invalid(value):
    """Test that double rejects values not convertible to float"""
    try:
        float(value)
        # If float() doesn't raise, double shouldn't either
        result = double(value)
        assert result == value
    except (ValueError, TypeError):
        # If float() raises, double should raise ValueError
        with pytest.raises(ValueError):
            double(value)

# Test 8: Round-trip property for numeric strings
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_double_string_round_trip(num):
    """Test that converting a float to string and back through double works"""
    str_num = str(num)
    result = double(str_num)
    assert result == str_num
    assert float(result) == pytest.approx(num, rel=1e-9)