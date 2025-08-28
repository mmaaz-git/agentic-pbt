#!/usr/bin/env python3
"""Edge case property-based tests for trino.mapper module using Hypothesis."""

import base64
import math
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import uuid

from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Import the mappers to test
from trino.mapper import (
    BooleanValueMapper,
    IntegerValueMapper,
    DoubleValueMapper,
    DecimalValueMapper,
    StringValueMapper,
    BinaryValueMapper,
    DateValueMapper,
    TimeValueMapper,
    ArrayValueMapper,
    MapValueMapper,
    UuidValueMapper,
    IntervalDayToSecondMapper,
    IntervalYearToMonthMapper,
    _fraction_to_decimal,
    _create_tzinfo,
    TimeWithTimeZoneValueMapper,
    TimestampValueMapper,
    TimestampWithTimeZoneValueMapper,
    RowValueMapper,
    NoOpValueMapper,
)
from trino.types import POWERS_OF_TEN
import trino.exceptions


# Test edge case: BooleanValueMapper with unexpected string values
@given(st.text().filter(lambda x: x.lower() not in ['true', 'false']))
@example("")  # Empty string
@example("yes")
@example("1")
@example("0")
@example("null")
@example("None")
@example("TRUE ")  # with trailing space
@example(" TRUE")  # with leading space
def test_boolean_invalid_strings(value):
    """BooleanValueMapper should raise ValueError for invalid string values."""
    mapper = BooleanValueMapper()
    if value.strip().lower() in ['true', 'false']:
        # These should work
        result = mapper.map(value)
        assert isinstance(result, bool)
    else:
        with pytest.raises(ValueError, match="Server sent unexpected value"):
            mapper.map(value)


# Test edge case: IntegerValueMapper with float strings
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_from_float_string(value):
    """IntegerValueMapper behavior with float string representations."""
    mapper = IntegerValueMapper()
    # According to the comment in the code, server won't send float values for integers
    # But the mapper will truncate them
    if value == int(value):  # If it's a whole number
        result = mapper.map(str(value))
        assert result == int(value)
    else:
        # The mapper will truncate
        result = mapper.map(str(value))
        assert result == int(value)


# Test edge case: DoubleValueMapper with invalid strings
@given(st.text().filter(lambda x: x not in ['Infinity', '-Infinity', 'NaN']))
@example("")
@example("inf")  # lowercase
@example("infinity")  # lowercase
@example("+Infinity")
def test_double_invalid_strings(value):
    """DoubleValueMapper behavior with various string inputs."""
    mapper = DoubleValueMapper()
    try:
        result = mapper.map(value)
        # If it doesn't raise, it should be a valid float conversion
        assert isinstance(result, float)
    except ValueError:
        # Some strings will raise ValueError when converting to float
        pass


# Test edge case: BinaryValueMapper with invalid base64
@given(st.text(alphabet='!@#$%^&*()', min_size=1))
def test_binary_invalid_base64(value):
    """BinaryValueMapper with invalid base64 strings."""
    mapper = BinaryValueMapper()
    try:
        result = mapper.map(value)
        # If it succeeds, it should return bytes
        assert isinstance(result, bytes)
    except Exception:
        # Invalid base64 will raise an exception
        pass


# Test edge case: DateValueMapper with invalid ISO format
@given(st.text())
@example("2023-13-01")  # Invalid month
@example("2023-01-32")  # Invalid day
@example("not-a-date")
@example("")
def test_date_invalid_iso(value):
    """DateValueMapper with invalid ISO format strings."""
    mapper = DateValueMapper()
    try:
        result = mapper.map(value)
        assert isinstance(result, date)
    except ValueError:
        # Invalid date strings will raise ValueError
        pass


# Test edge case: _fraction_to_decimal with empty string
def test_fraction_to_decimal_edge_cases():
    """Test _fraction_to_decimal with edge cases."""
    # Empty string
    assert _fraction_to_decimal('') == Decimal(0)
    
    # Single digit
    assert _fraction_to_decimal('5') == Decimal('0.5')
    
    # Multiple digits
    assert _fraction_to_decimal('123') == Decimal('0.123')
    
    # Leading zeros
    assert _fraction_to_decimal('00123') == Decimal('0.00123')


# Test edge case: IntervalDayToSecondMapper with overflow
def test_interval_overflow():
    """IntervalDayToSecondMapper should handle overflow gracefully."""
    mapper = IntervalDayToSecondMapper()
    
    # Test very large values that might cause overflow
    large_interval = "999999999 23:59:59.999"
    try:
        result = mapper.map(large_interval)
        assert isinstance(result, timedelta)
    except trino.exceptions.TrinoDataError as e:
        # Should raise TrinoDataError for overflow
        assert "exceeds the maximum or minimum limit" in str(e)


# Test edge case: IntervalYearToMonthMapper with negative values
@given(
    st.integers(min_value=0, max_value=999),
    st.integers(min_value=0, max_value=11)
)
def test_interval_year_month_negative(years, months):
    """IntervalYearToMonthMapper should handle negative intervals."""
    mapper = IntervalYearToMonthMapper()
    
    # Positive interval
    positive_str = f"{years}-{months}"
    result = mapper.map(positive_str)
    assert result.years == years
    assert result.months == months
    
    # Negative interval
    if years > 0 or months > 0:
        negative_str = f"-{years}-{months}"
        result = mapper.map(negative_str)
        assert result.years == -years
        assert result.months == -months


# Test edge case: ArrayValueMapper with nested arrays
def test_nested_array_mapper():
    """ArrayValueMapper with nested arrays."""
    inner_mapper = ArrayValueMapper(IntegerValueMapper())
    outer_mapper = ArrayValueMapper(inner_mapper)
    
    nested_data = [[1, 2, 3], [4, 5], [], [6]]
    result = outer_mapper.map(nested_data)
    assert result == nested_data
    
    # With None values
    nested_with_none = [[1, None, 3], None, [None]]
    result = outer_mapper.map(nested_with_none)
    assert result == nested_with_none


# Test edge case: MapValueMapper with complex keys and values
def test_complex_map_mapper():
    """MapValueMapper with complex nested structures."""
    # Map with array values
    key_mapper = StringValueMapper()
    value_mapper = ArrayValueMapper(IntegerValueMapper())
    mapper = MapValueMapper(key_mapper, value_mapper)
    
    data = {
        "key1": [1, 2, 3],
        "key2": [],
        "key3": [4, None, 5]
    }
    result = mapper.map(data)
    assert result == data


# Test edge case: _create_tzinfo with various timezone formats
@given(st.sampled_from([
    "+00:00", "+01:00", "-01:00", "+05:30", "-05:30",
    "+12:00", "-12:00", "+23:59", "-23:59"
]))
def test_create_tzinfo_offsets(tz_str):
    """Test _create_tzinfo with various offset formats."""
    tzinfo = _create_tzinfo(tz_str)
    assert tzinfo is not None


def test_create_tzinfo_named():
    """Test _create_tzinfo with named timezones."""
    # Test with common timezone names
    for tz_name in ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]:
        try:
            tzinfo = _create_tzinfo(tz_name)
            assert tzinfo is not None
        except Exception:
            # Some timezone names might not be available
            pass


# Test edge case: TimeValueMapper with different precisions
@given(st.integers(min_value=0, max_value=12))
def test_time_mapper_precision(precision):
    """TimeValueMapper should handle different precision values."""
    mapper = TimeValueMapper(precision)
    
    # Test with a time value with fractional seconds
    time_str = "12:34:56.123456789"
    result = mapper.map(time_str)
    assert isinstance(result, time)


# Test edge case: RowValueMapper with missing field names
def test_row_mapper_missing_names():
    """RowValueMapper should handle missing field names."""
    mappers = [IntegerValueMapper(), StringValueMapper(), BooleanValueMapper()]
    names = [None, "field2", None]  # Some names are None
    types = ["integer", "varchar", "boolean"]
    
    mapper = RowValueMapper(mappers, names, types)
    data = [42, "test", True]
    result = mapper.map(data)
    
    assert len(result) == 3
    assert result[0] == 42
    assert result[1] == "test"
    assert result[2] == True
    
    # Should be able to access by name for non-None names
    assert result.field2 == "test"


# Test edge case: RowValueMapper with duplicate field names
def test_row_mapper_duplicate_names():
    """RowValueMapper should handle duplicate field names."""
    mappers = [IntegerValueMapper(), IntegerValueMapper(), IntegerValueMapper()]
    names = ["field", "field", "other"]  # Duplicate names
    types = ["integer", "integer", "integer"]
    
    mapper = RowValueMapper(mappers, names, types)
    data = [1, 2, 3]
    result = mapper.map(data)
    
    assert len(result) == 3
    assert result[0] == 1
    assert result[1] == 2
    assert result[2] == 3
    
    # Accessing duplicate name should raise ValueError
    with pytest.raises(ValueError, match="Ambiguous row field reference"):
        _ = result.field


# Test edge case: NoOpValueMapper returns values unchanged
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=True),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_noop_mapper(value):
    """NoOpValueMapper should return values unchanged."""
    mapper = NoOpValueMapper()
    result = mapper.map(value)
    assert result is value  # Should be the exact same object


# Test edge case: TimestampValueMapper with different precisions
@given(st.integers(min_value=0, max_value=12))
def test_timestamp_mapper_precision(precision):
    """TimestampValueMapper should handle different precision values."""
    mapper = TimestampValueMapper(precision)
    
    # Test with a timestamp value with fractional seconds
    timestamp_str = "2023-01-15 12:34:56.123456789"
    result = mapper.map(timestamp_str)
    assert isinstance(result, datetime)


# Test edge case: TimestampWithTimeZoneValueMapper with various timezones
def test_timestamp_with_tz_mapper():
    """TimestampWithTimeZoneValueMapper should handle various timezone formats."""
    mapper = TimestampWithTimeZoneValueMapper(precision=6)
    
    # Test with offset timezone
    timestamp_str = "2023-01-15 12:34:56.123456 +05:30"
    result = mapper.map(timestamp_str)
    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    
    # Test with UTC
    timestamp_str = "2023-01-15 12:34:56.123456 UTC"
    result = mapper.map(timestamp_str)
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


# Test edge case: TimeWithTimeZoneValueMapper
def test_time_with_tz_mapper():
    """TimeWithTimeZoneValueMapper should handle time with timezone."""
    mapper = TimeWithTimeZoneValueMapper(precision=3)
    
    # Test with offset timezone
    time_str = "12:34:56.123+05:30"
    result = mapper.map(time_str)
    assert isinstance(result, time)
    assert result.tzinfo is not None


# Test for DoubleValueMapper with very large/small numbers
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
def test_double_extreme_values(value):
    """DoubleValueMapper should handle extreme float values."""
    mapper = DoubleValueMapper()
    result = mapper.map(value)
    if not math.isnan(result):  # NaN != NaN
        assert math.isclose(result, value, rel_tol=1e-9) or (math.isinf(result) and math.isinf(value))


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])