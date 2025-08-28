import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.transfer as transfer
import pytest


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_identity_property_floats(x):
    """double() should return input unchanged for float inputs"""
    result = transfer.double(x)
    assert result == x
    assert type(result) == type(x)


@given(st.integers())
def test_double_identity_property_integers(x):
    """double() should return input unchanged for integer inputs"""
    result = transfer.double(x)
    assert result == x
    assert type(result) == type(x)


@given(st.text(min_size=1).filter(lambda s: s.replace('.', '').replace('-', '').replace('+', '').isdigit()))
def test_double_identity_property_numeric_strings(x):
    """double() should return input unchanged for numeric string inputs"""
    try:
        float(x)  # Only test strings that can be converted to float
        result = transfer.double(x)
        assert result == x
        assert type(result) == type(x)
    except ValueError:
        pass  # Skip non-numeric strings


@given(st.one_of(st.floats(allow_nan=False, allow_infinity=False), 
                  st.integers(),
                  st.text(min_size=1).filter(lambda s: s.replace('.', '').replace('-', '').isdigit())))
def test_double_idempotence(x):
    """double(double(x)) should equal double(x) for valid inputs"""
    try:
        first_result = transfer.double(x)
        second_result = transfer.double(first_result)
        assert first_result == second_result
    except ValueError:
        pass  # Expected for invalid inputs


@given(st.integers())
def test_integer_identity_property_integers(x):
    """integer() should return input unchanged for integer inputs"""
    result = transfer.integer(x)
    assert result == x
    assert type(result) == type(x)


@given(st.text(min_size=1).filter(lambda s: s.replace('-', '').replace('+', '').isdigit()))
def test_integer_identity_property_numeric_strings(x):
    """integer() should return input unchanged for integer-convertible strings"""
    try:
        int(x)  # Only test strings that can be converted to int
        result = transfer.integer(x)
        assert result == x
        assert type(result) == type(x)
    except ValueError:
        pass  # Skip non-integer strings


@given(st.one_of(st.integers(),
                  st.text(min_size=1).filter(lambda s: s.replace('-', '').isdigit())))
def test_integer_idempotence(x):
    """integer(integer(x)) should equal integer(x) for valid inputs"""
    try:
        first_result = transfer.integer(x)
        second_result = transfer.integer(first_result)
        assert first_result == second_result
    except ValueError:
        pass  # Expected for invalid inputs


@given(st.text())
def test_validate_homedirectory_type_valid_values(x):
    """validate_homedirectory_type should only accept 'LOGICAL' or 'PATH'"""
    if x in ["LOGICAL", "PATH"]:
        result = transfer.validate_homedirectory_type(x)
        assert result == x  # Should return input unchanged
    else:
        with pytest.raises(ValueError) as exc_info:
            transfer.validate_homedirectory_type(x)
        assert "User HomeDirectoryType must be one of:" in str(exc_info.value)


@given(st.sampled_from(["LOGICAL", "PATH"]))
def test_validate_homedirectory_type_identity(x):
    """validate_homedirectory_type should return valid inputs unchanged"""
    result = transfer.validate_homedirectory_type(x)
    assert result == x
    assert type(result) == type(x)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_double_handles_small_floats(x):
    """double() should handle small float values correctly"""
    result = transfer.double(x)
    assert result == x


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_float_string_roundtrip(x):
    """double() should handle float->str->double conversion"""
    str_x = str(x)
    result = transfer.double(str_x)
    assert result == str_x
    # Verify the string can still be converted back to float
    assert math.isclose(float(result), x, rel_tol=1e-9)


@given(st.integers())
def test_integer_string_roundtrip(x):
    """integer() should handle int->str->integer conversion"""
    str_x = str(x)
    result = transfer.integer(str_x)
    assert result == str_x
    # Verify the string can still be converted back to int
    assert int(result) == x


@given(st.lists(st.sampled_from(["LOGICAL", "PATH"]), min_size=1))
def test_validate_homedirectory_type_multiple_calls(values):
    """validate_homedirectory_type should handle multiple valid values consistently"""
    for value in values:
        result = transfer.validate_homedirectory_type(value)
        assert result == value


@given(st.one_of(st.none(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers())))
def test_double_rejects_non_numeric(x):
    """double() should raise ValueError for non-numeric types"""
    with pytest.raises(ValueError) as exc_info:
        transfer.double(x)
    assert "is not a valid double" in str(exc_info.value)


@given(st.one_of(st.none(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers())))
def test_integer_rejects_non_numeric(x):
    """integer() should raise ValueError for non-numeric types"""
    with pytest.raises(ValueError) as exc_info:
        transfer.integer(x)
    assert "is not a valid integer" in str(exc_info.value)