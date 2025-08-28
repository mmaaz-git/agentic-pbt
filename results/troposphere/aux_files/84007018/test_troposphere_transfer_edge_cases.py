import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.transfer as transfer
import pytest


@given(st.binary())
def test_double_with_bytes(x):
    """Test double() with byte strings - type hints suggest bytes are acceptable"""
    try:
        # Try to convert bytes to see if it's numeric
        float(x)
        result = transfer.double(x)
        assert result == x
        assert type(result) == type(x)
    except (ValueError, TypeError):
        # Should raise ValueError with specific message
        with pytest.raises(ValueError) as exc_info:
            transfer.double(x)
        assert "is not a valid double" in str(exc_info.value)


@given(st.binary())
def test_integer_with_bytes(x):
    """Test integer() with byte strings - type hints suggest bytes are acceptable"""
    try:
        # Try to convert bytes to see if it's numeric
        int(x)
        result = transfer.integer(x)
        assert result == x
        assert type(result) == type(x)
    except (ValueError, TypeError):
        # Should raise ValueError with specific message
        with pytest.raises(ValueError) as exc_info:
            transfer.integer(x)
        assert "is not a valid integer" in str(exc_info.value)


@given(st.sampled_from(["1e10", "1E10", "1.5e-5", "3.14E2", "1e308", "-1e308"]))
def test_double_scientific_notation(x):
    """Test double() with scientific notation strings"""
    result = transfer.double(x)
    assert result == x
    # Verify it's actually a valid float string
    float(result)


@given(st.sampled_from(["+5", "-0", "+0", "   5   ", "\t10\n", "+123", "-456"]))
def test_integer_special_formats(x):
    """Test integer() with special numeric string formats"""
    try:
        int(x)  # Check if Python accepts it
        result = transfer.integer(x)
        assert result == x
    except ValueError:
        with pytest.raises(ValueError):
            transfer.integer(x)


@given(st.sampled_from(["+5.5", "-0.0", "+0.0", "   5.5   ", "\t10.5\n", "+123.456", "-456.789"]))
def test_double_special_formats(x):
    """Test double() with special numeric string formats"""
    try:
        float(x)  # Check if Python accepts it
        result = transfer.double(x)
        assert result == x
    except ValueError:
        with pytest.raises(ValueError):
            transfer.double(x)


@given(st.integers(min_value=10**100, max_value=10**200))
def test_integer_very_large_numbers(x):
    """Test integer() with very large integers"""
    result = transfer.integer(x)
    assert result == x
    
    # Also test as string
    str_x = str(x)
    result_str = transfer.integer(str_x)
    assert result_str == str_x


@given(st.sampled_from(["infinity", "inf", "-inf", "nan", "NaN", "Infinity", "-Infinity"]))
def test_double_special_float_strings(x):
    """Test double() with special float value strings"""
    try:
        float(x)  # Check if Python accepts it
        result = transfer.double(x)
        assert result == x
    except ValueError:
        with pytest.raises(ValueError):
            transfer.double(x)


@given(st.sampled_from(["1.0", "2.0", "100.0", "-5.0"]))
def test_integer_rejects_float_strings(x):
    """Test that integer() properly handles/rejects float-like strings"""
    # These can be converted to float but not directly to int
    with pytest.raises(ValueError) as exc_info:
        transfer.integer(x)
    assert "is not a valid integer" in str(exc_info.value)


@given(st.sampled_from(["0x10", "0o10", "0b10"]))
def test_integer_alternate_bases(x):
    """Test integer() with alternate base representations"""
    try:
        int(x, 0)  # Python can parse these with base=0
        # But int(x) without base should fail
        int(x)
    except ValueError:
        # Should reject these
        with pytest.raises(ValueError) as exc_info:
            transfer.integer(x)
        assert "is not a valid integer" in str(exc_info.value)


@given(st.sampled_from(["①", "②", "③", "一", "二", "三", "١", "٢", "٣"]))
def test_unicode_digits(x):
    """Test with Unicode digit characters"""
    # These are digit characters but not ASCII
    with pytest.raises(ValueError) as exc_info:
        transfer.double(x)
    assert "is not a valid double" in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        transfer.integer(x)
    assert "is not a valid integer" in str(exc_info.value)


@given(st.sampled_from(["", " ", "\t", "\n", "   "]))
def test_empty_and_whitespace_strings(x):
    """Test with empty and whitespace-only strings"""
    with pytest.raises(ValueError) as exc_info:
        transfer.double(x)
    assert "is not a valid double" in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        transfer.integer(x)
    assert "is not a valid integer" in str(exc_info.value)


@given(st.booleans())
def test_boolean_values(x):
    """Test with boolean values - interesting because bool is subclass of int in Python"""
    # In Python, bool is a subclass of int, so int(True) == 1, int(False) == 0
    result_int = transfer.integer(x)
    assert result_int == x
    assert type(result_int) == bool  # Should preserve type
    
    result_double = transfer.double(x)
    assert result_double == x
    assert type(result_double) == bool  # Should preserve type


class CustomInt(int):
    """Custom int subclass for testing"""
    pass


class CustomFloat(float):
    """Custom float subclass for testing"""
    pass


@given(st.integers().map(CustomInt))
def test_integer_custom_int_subclass(x):
    """Test integer() with custom int subclass"""
    result = transfer.integer(x)
    assert result == x
    assert type(result) == type(x)  # Should preserve exact type


@given(st.floats(allow_nan=False, allow_infinity=False).map(CustomFloat))
def test_double_custom_float_subclass(x):
    """Test double() with custom float subclass"""
    result = transfer.double(x)
    assert result == x
    assert type(result) == type(x)  # Should preserve exact type