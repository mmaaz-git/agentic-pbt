#!/usr/bin/env python3
"""Property-based tests for the trino module using Hypothesis."""

import base64
import math
from datetime import datetime, time, timedelta
from decimal import Decimal
from hypothesis import assume, given, strategies as st, settings

# Import trino modules under test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.mapper import (
    BinaryValueMapper, BooleanValueMapper, DoubleValueMapper,
    IntegerValueMapper, DecimalValueMapper, StringValueMapper,
    _fraction_to_decimal, _create_tzinfo,
    TimeValueMapper, TimestampValueMapper
)
from trino.types import Time, Timestamp, POWERS_OF_TEN


# Test 1: BinaryValueMapper round-trip property
@given(st.binary())
def test_binary_mapper_round_trip(data):
    """Test that BinaryValueMapper correctly decodes base64-encoded binary data."""
    mapper = BinaryValueMapper()
    # Encode the binary data to base64 string as the server would send it
    encoded = base64.b64encode(data).decode('utf-8')
    # Map it back through the mapper
    result = mapper.map(encoded)
    assert result == data, f"Round-trip failed: {data} != {result}"


# Test 2: BooleanValueMapper string parsing
@given(st.one_of(
    st.just('true'), st.just('false'),
    st.just('True'), st.just('False'),
    st.just('TRUE'), st.just('FALSE'),
    st.just('tRuE'), st.just('fAlSe'),
    st.booleans()
))
def test_boolean_mapper_parsing(value):
    """Test that BooleanValueMapper correctly handles various boolean representations."""
    mapper = BooleanValueMapper()
    result = mapper.map(value)
    if isinstance(value, bool):
        assert result == value
    elif str(value).lower() == 'true':
        assert result is True
    elif str(value).lower() == 'false':
        assert result is False


# Test 3: DoubleValueMapper special values
@given(st.one_of(
    st.just('Infinity'),
    st.just('-Infinity'),
    st.just('NaN'),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet='0123456789.-+eE', min_size=1, max_size=20).filter(
        lambda x: x not in ['Infinity', '-Infinity', 'NaN'] and x.count('.') <= 1
    )
))
def test_double_mapper_special_values(value):
    """Test that DoubleValueMapper correctly handles special float values."""
    mapper = DoubleValueMapper()
    
    if value == 'Infinity':
        result = mapper.map(value)
        assert math.isinf(result) and result > 0
    elif value == '-Infinity':
        result = mapper.map(value)
        assert math.isinf(result) and result < 0
    elif value == 'NaN':
        result = mapper.map(value)
        assert math.isnan(result)
    else:
        try:
            # If it's a valid float string or float, it should convert
            expected = float(value)
            result = mapper.map(value)
            if math.isnan(expected):
                assert math.isnan(result)
            else:
                assert result == expected
        except (ValueError, OverflowError):
            # Invalid float strings should raise an error
            pass


# Test 4: IntegerValueMapper preservation
@given(st.integers())
def test_integer_mapper_preservation(value):
    """Test that IntegerValueMapper preserves integer values."""
    mapper = IntegerValueMapper()
    result = mapper.map(value)
    assert result == value
    assert isinstance(result, int)


# Test 5: IntegerValueMapper string conversion
@given(st.integers().map(str))
def test_integer_mapper_string_conversion(value_str):
    """Test that IntegerValueMapper correctly converts string integers."""
    mapper = IntegerValueMapper()
    result = mapper.map(value_str)
    assert result == int(value_str)
    assert isinstance(result, int)


# Test 6: DecimalValueMapper precision preservation
@given(st.decimals(allow_nan=False, allow_infinity=False))
def test_decimal_mapper_precision(value):
    """Test that DecimalValueMapper preserves decimal precision exactly."""
    mapper = DecimalValueMapper()
    # Convert to string to simulate server sending it
    value_str = str(value)
    result = mapper.map(value_str)
    assert result == Decimal(value_str)
    assert isinstance(result, Decimal)


# Test 7: StringValueMapper always returns strings
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False),
    st.booleans()
))
def test_string_mapper_conversion(value):
    """Test that StringValueMapper always returns string representation."""
    mapper = StringValueMapper()
    result = mapper.map(value)
    assert result == str(value)
    assert isinstance(result, str)


# Test 8: _fraction_to_decimal mathematical properties
@given(st.text(alphabet='0123456789', min_size=0, max_size=12))
def test_fraction_to_decimal_properties(fractional_str):
    """Test mathematical properties of _fraction_to_decimal function."""
    result = _fraction_to_decimal(fractional_str)
    
    # Empty string should give 0
    if fractional_str == '':
        assert result == 0
    else:
        # The result should be the fractional value divided by the appropriate power of 10
        expected = Decimal(fractional_str or 0) / POWERS_OF_TEN[len(fractional_str)]
        assert result == expected
        # Result should always be less than 1 for non-empty strings
        assert result < 1
        # Result should be non-negative
        assert result >= 0


# Test 9: _create_tzinfo offset parsing
@given(
    st.one_of(
        # Positive offsets
        st.tuples(st.just('+'), st.integers(0, 23), st.integers(0, 59)),
        # Negative offsets
        st.tuples(st.just('-'), st.integers(0, 23), st.integers(0, 59))
    )
)
def test_create_tzinfo_offset_parsing(offset_tuple):
    """Test that _create_tzinfo correctly parses timezone offset strings."""
    sign, hours, minutes = offset_tuple
    timezone_str = f"{sign}{hours:02d}:{minutes:02d}"
    
    tzinfo = _create_tzinfo(timezone_str)
    
    # Calculate expected offset
    total_minutes = hours * 60 + minutes
    if sign == '-':
        total_minutes = -total_minutes
    expected_offset = timedelta(minutes=total_minutes)
    
    # Verify the timezone has the correct offset
    # Use a reference datetime to get the offset
    ref_dt = datetime(2024, 1, 1, tzinfo=tzinfo)
    assert ref_dt.utcoffset() == expected_offset


# Test 10: Null value handling across all mappers
@given(st.just(None))
def test_all_mappers_handle_none(value):
    """Test that all value mappers correctly handle None values."""
    mappers = [
        BinaryValueMapper(),
        BooleanValueMapper(),
        IntegerValueMapper(),
        DoubleValueMapper(),
        DecimalValueMapper(),
        StringValueMapper(),
    ]
    
    for mapper in mappers:
        result = mapper.map(value)
        assert result is None, f"{mapper.__class__.__name__} did not return None for None input"


# Test 11: Time rounding properties
@given(
    st.integers(0, 23),  # hours
    st.integers(0, 59),  # minutes  
    st.integers(0, 59),  # seconds
    st.integers(0, 999999),  # microseconds as fractional part
    st.integers(0, 12)  # precision
)
def test_time_rounding_properties(hours, minutes, seconds, fractional_microseconds, precision):
    """Test that Time.round_to maintains correct precision constraints."""
    # Create a time object
    base_time = time(hours, minutes, seconds)
    # Convert microseconds to decimal fraction
    fractional_seconds = Decimal(fractional_microseconds) / Decimal(1000000)
    
    time_obj = Time(base_time, fractional_seconds)
    rounded = time_obj.round_to(precision)
    
    # The rounded value should have at most 'precision' decimal places
    # (or 6 if precision > 6, since Python time only supports microseconds)
    effective_precision = min(precision, 6)
    
    # Get the fractional part after rounding
    rounded_fraction = rounded._remaining_fractional_seconds
    
    # Check that the fraction has been appropriately rounded
    if effective_precision == 0:
        # Should be rounded to nearest second
        assert rounded_fraction == 0 or rounded_fraction == 1
    else:
        # Check the number of significant decimal places
        # The fraction should be quantized to the appropriate precision
        scale = 10 ** effective_precision
        # This should be an integer when multiplied by the scale
        scaled = rounded_fraction * scale
        # Allow for floating point imprecision
        assert abs(scaled - round(scaled)) < Decimal('0.00001')


# Test 12: Timestamp rounding properties
@given(
    st.datetimes(min_value=datetime(1970, 1, 1), max_value=datetime(2100, 1, 1)),
    st.integers(0, 999999999),  # nanoseconds as fractional part
    st.integers(0, 12)  # precision
)
def test_timestamp_rounding_properties(dt, fractional_nanoseconds, precision):
    """Test that Timestamp.round_to maintains correct precision constraints."""
    # Convert nanoseconds to decimal fraction of a second
    fractional_seconds = Decimal(fractional_nanoseconds) / Decimal(1000000000)
    
    timestamp_obj = Timestamp(dt, fractional_seconds)
    rounded = timestamp_obj.round_to(precision)
    
    # The rounded value should have at most 'precision' decimal places
    # (or 6 if precision > 6, since Python datetime only supports microseconds)
    effective_precision = min(precision, 6)
    
    # Get the fractional part after rounding
    rounded_fraction = rounded._remaining_fractional_seconds
    
    # Check that the fraction has been appropriately rounded
    if effective_precision == 0:
        # Should be rounded to nearest second
        assert rounded_fraction == 0 or rounded_fraction == 1
    else:
        # Check the number of significant decimal places
        scale = 10 ** effective_precision
        scaled = rounded_fraction * scale
        # Allow for floating point imprecision
        assert abs(scaled - round(scaled)) < Decimal('0.00001')


if __name__ == "__main__":
    print("Running property-based tests for trino module...")
    import pytest
    pytest.main([__file__, "-v"])