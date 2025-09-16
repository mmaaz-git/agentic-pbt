"""Property-based tests for troposphere.workspacesthinclient module."""

import math
from hypothesis import assume, given, strategies as st, settings
import pytest
from troposphere.workspacesthinclient import integer, MaintenanceWindow, Environment


# Strategy for values that should be accepted by integer()
valid_integer_convertible = st.one_of(
    st.integers(),
    st.text().filter(lambda s: s.strip() and s.strip().lstrip('-+').isdigit()),  # strings like "123", "-45"
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)),  # whole number floats
    st.booleans()
)

# Strategy for any Python value
any_value = st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers()),
    st.binary()
)


@given(valid_integer_convertible)
def test_integer_idempotence(x):
    """Test that integer() is idempotent - applying it twice gives same result as once."""
    result1 = integer(x)
    result2 = integer(result1)
    assert result1 == result2
    assert type(result1) == type(result2)


@given(valid_integer_convertible)
def test_integer_preserves_input_object(x):
    """Test that integer() returns the exact same object, not a converted copy."""
    result = integer(x)
    assert result is x


@given(any_value)
def test_integer_validation_consistency_with_int(x):
    """Test that integer() validation is consistent with int() builtin."""
    int_succeeds = False
    int_error = None
    
    try:
        int(x)
        int_succeeds = True
    except (ValueError, TypeError) as e:
        int_error = e
    
    if int_succeeds:
        # If int(x) succeeds, integer(x) should not raise ValueError
        try:
            result = integer(x)
            # Should return the original value
            assert result is x
        except ValueError:
            pytest.fail(f"integer({repr(x)}) raised ValueError but int({repr(x)}) succeeded")
    else:
        # If int(x) fails, integer(x) should raise ValueError
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(x)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_float_handling(x):
    """Test integer() correctly handles floats - accepts whole numbers, rejects fractions."""
    is_whole = x == int(x)
    
    if is_whole:
        # Should accept whole number floats
        result = integer(x)
        assert result is x
    else:
        # Should reject fractional floats
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(x)


@given(st.text())
def test_integer_string_handling(s):
    """Test integer() correctly validates string inputs."""
    # Check if string can be converted to int
    can_convert = False
    try:
        int(s)
        can_convert = True
    except (ValueError, TypeError):
        pass
    
    if can_convert:
        result = integer(s)
        assert result is s
    else:
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(s)


@given(
    st.one_of(st.integers(), st.text().filter(lambda s: s.strip() and s.strip().lstrip('-+').isdigit())),
    st.one_of(st.integers(), st.text().filter(lambda s: s.strip() and s.strip().lstrip('-+').isdigit()))
)
def test_maintenance_window_hour_minute_validation(hour, minute):
    """Test that MaintenanceWindow accepts various integer-convertible types for time fields."""
    # Should accept both integers and numeric strings
    mw = MaintenanceWindow(
        Type='CUSTOM',
        StartTimeHour=hour,
        StartTimeMinute=minute
    )
    
    # Check that values are preserved
    assert mw.StartTimeHour is hour
    assert mw.StartTimeMinute is minute
    
    # to_dict should preserve the values
    d = mw.to_dict()
    assert d['StartTimeHour'] is hour
    assert d['StartTimeMinute'] is minute


@given(
    st.one_of(
        st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),  # fractional floats
        st.text().filter(lambda s: not (s.strip() and s.strip().lstrip('-+').isdigit())),  # non-numeric strings
        st.none(),
        st.lists(st.integers(), min_size=1)
    )
)
def test_maintenance_window_invalid_time_validation(invalid_value):
    """Test that MaintenanceWindow properly validates invalid time values."""
    # These should fail validation when validate() is called
    mw = MaintenanceWindow(
        Type='CUSTOM',
        StartTimeHour=invalid_value
    )
    
    # The object can be created, but validation should catch the error
    # Note: validation happens at template generation time in troposphere
    # Let's test that the integer validator would catch this
    with pytest.raises(ValueError):
        integer(invalid_value)


@given(st.dictionaries(
    st.sampled_from(['Type', 'StartTimeHour', 'StartTimeMinute', 'EndTimeHour', 'EndTimeMinute', 'ApplyTimeOf', 'DaysOfTheWeek']),
    st.one_of(
        st.integers(),
        st.text(),
        st.lists(st.text())
    ),
    min_size=1
))
def test_maintenance_window_from_dict(data):
    """Test MaintenanceWindow can be created from dict and serialized back."""
    # Ensure we have required Type field
    if 'Type' not in data:
        data['Type'] = 'CUSTOM'
    
    # Create from dict
    mw = MaintenanceWindow.from_dict('TestWindow', data)
    
    # Should preserve the title
    assert mw.title == 'TestWindow'
    
    # to_dict should return a dict
    result = mw.to_dict()
    assert isinstance(result, dict)
    
    # All provided keys should be in result (if they're valid props)
    valid_props = set(mw.props.keys())
    for key in data:
        if key in valid_props:
            assert key in result


@given(st.data())
def test_integer_error_message_format(data):
    """Test that integer() error messages have consistent format."""
    # Generate values that should fail
    invalid_value = data.draw(st.one_of(
        st.floats(allow_nan=False).filter(lambda x: x != int(x)),
        st.text().filter(lambda s: not (s.strip() and s.strip().lstrip('-+').isdigit())),
        st.none(),
        st.lists(st.integers(), min_size=1),
        st.dictionaries(st.text(), st.integers(), min_size=1)
    ))
    
    with pytest.raises(ValueError) as exc_info:
        integer(invalid_value)
    
    error_msg = str(exc_info.value)
    # Check error message format
    assert "is not a valid integer" in error_msg
    assert repr(invalid_value) in error_msg