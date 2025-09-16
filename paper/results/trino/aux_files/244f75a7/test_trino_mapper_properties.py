#!/usr/bin/env python3
"""Property-based tests for trino.mapper module using Hypothesis."""

import base64
import math
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import uuid

from hypothesis import given, strategies as st, assume, settings
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
    _fraction_to_decimal,
)
from trino.types import POWERS_OF_TEN


# Test 1: None handling invariant - All mappers should return None for None input
@given(st.just(None))
def test_none_handling_invariant(value):
    """All mappers should return None when given None input."""
    mappers = [
        BooleanValueMapper(),
        IntegerValueMapper(),
        DoubleValueMapper(),
        DecimalValueMapper(),
        StringValueMapper(),
        BinaryValueMapper(),
        DateValueMapper(),
        TimeValueMapper(precision=3),
        UuidValueMapper(),
        IntervalDayToSecondMapper(),
        ArrayValueMapper(StringValueMapper()),
        MapValueMapper(StringValueMapper(), StringValueMapper()),
    ]
    
    for mapper in mappers:
        assert mapper.map(value) is None


# Test 2: BinaryValueMapper round-trip property
@given(st.binary(min_size=0, max_size=1000))
def test_binary_round_trip(data):
    """BinaryValueMapper should correctly decode base64 encoded data."""
    mapper = BinaryValueMapper()
    # Encode the binary data to base64 string (as server would send)
    encoded = base64.b64encode(data).decode('utf8')
    # Map it back through the mapper
    result = mapper.map(encoded)
    assert result == data


# Test 3: BooleanValueMapper case insensitivity
@given(st.sampled_from(['true', 'TRUE', 'True', 'TrUe', 'false', 'FALSE', 'False', 'FaLsE']))
def test_boolean_case_insensitive(value):
    """BooleanValueMapper should handle 'true'/'false' case-insensitively."""
    mapper = BooleanValueMapper()
    result = mapper.map(value)
    expected = value.lower() == 'true'
    assert result == expected


# Test 4: BooleanValueMapper handles actual booleans
@given(st.booleans())
def test_boolean_actual_bool(value):
    """BooleanValueMapper should handle actual boolean values."""
    mapper = BooleanValueMapper()
    result = mapper.map(value)
    assert result == value


# Test 5: DoubleValueMapper special values
@given(st.sampled_from(['Infinity', '-Infinity', 'NaN']))
def test_double_special_values(value):
    """DoubleValueMapper should handle special float values."""
    mapper = DoubleValueMapper()
    result = mapper.map(value)
    
    if value == 'Infinity':
        assert math.isinf(result) and result > 0
    elif value == '-Infinity':
        assert math.isinf(result) and result < 0
    elif value == 'NaN':
        assert math.isnan(result)


# Test 6: DoubleValueMapper regular floats
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_regular_values(value):
    """DoubleValueMapper should handle regular float values."""
    mapper = DoubleValueMapper()
    # Convert to string as server would send it
    result = mapper.map(str(value))
    assert math.isclose(result, value, rel_tol=1e-9)


# Test 7: _fraction_to_decimal mathematical correctness
@given(st.text(alphabet='0123456789', min_size=1, max_size=12))
def test_fraction_to_decimal(fractional_str):
    """_fraction_to_decimal should correctly convert fractional strings to Decimal."""
    result = _fraction_to_decimal(fractional_str)
    expected = Decimal(fractional_str) / POWERS_OF_TEN[len(fractional_str)]
    assert result == expected


# Test 8: _fraction_to_decimal with empty string
def test_fraction_to_decimal_empty():
    """_fraction_to_decimal should handle empty string correctly."""
    result = _fraction_to_decimal('')
    assert result == Decimal(0)


# Test 9: ArrayValueMapper length preservation
@given(st.lists(st.integers()))
def test_array_length_preservation(values):
    """ArrayValueMapper should preserve the length of arrays."""
    mapper = ArrayValueMapper(IntegerValueMapper())
    result = mapper.map(values)
    assert len(result) == len(values)
    assert all(result[i] == values[i] for i in range(len(values)))


# Test 10: ArrayValueMapper with nested None values
@given(st.lists(st.one_of(st.none(), st.integers())))
def test_array_with_nones(values):
    """ArrayValueMapper should handle None values in arrays."""
    mapper = ArrayValueMapper(IntegerValueMapper())
    result = mapper.map(values)
    assert len(result) == len(values)
    for i in range(len(values)):
        if values[i] is None:
            assert result[i] is None
        else:
            assert result[i] == values[i]


# Test 11: MapValueMapper key preservation
@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_map_key_preservation(data):
    """MapValueMapper should preserve all dictionary keys."""
    mapper = MapValueMapper(StringValueMapper(), IntegerValueMapper())
    result = mapper.map(data)
    assert set(result.keys()) == set(data.keys())
    for key in data:
        assert result[key] == data[key]


# Test 12: MapValueMapper with None values
@given(st.dictionaries(st.text(min_size=1), st.one_of(st.none(), st.integers())))
def test_map_with_none_values(data):
    """MapValueMapper should handle None values in dictionaries."""
    mapper = MapValueMapper(StringValueMapper(), IntegerValueMapper())
    result = mapper.map(data)
    assert set(result.keys()) == set(data.keys())
    for key in data:
        assert result[key] == data[key]


# Test 13: UuidValueMapper round-trip
@given(st.uuids())
def test_uuid_round_trip(value):
    """UuidValueMapper should correctly parse UUID strings."""
    mapper = UuidValueMapper()
    # Convert UUID to string as server would send it
    uuid_str = str(value)
    result = mapper.map(uuid_str)
    assert result == value
    assert str(result) == uuid_str


# Test 14: IntegerValueMapper handles string integers
@given(st.integers())
def test_integer_from_string(value):
    """IntegerValueMapper should handle string representations of integers."""
    mapper = IntegerValueMapper()
    result = mapper.map(str(value))
    assert result == value


# Test 15: DecimalValueMapper precision preservation
@given(st.decimals(allow_nan=False, allow_infinity=False))
def test_decimal_precision(value):
    """DecimalValueMapper should preserve decimal precision."""
    mapper = DecimalValueMapper()
    result = mapper.map(str(value))
    assert result == value


# Test 16: DateValueMapper ISO format parsing
@given(st.dates())
def test_date_iso_format(value):
    """DateValueMapper should correctly parse ISO format dates."""
    mapper = DateValueMapper()
    iso_str = value.isoformat()
    result = mapper.map(iso_str)
    assert result == value


# Test 17: IntervalDayToSecondMapper positive intervals
@given(
    st.integers(min_value=0, max_value=999),  # days
    st.integers(min_value=0, max_value=23),   # hours
    st.integers(min_value=0, max_value=59),   # minutes
    st.integers(min_value=0, max_value=59),   # seconds
    st.integers(min_value=0, max_value=999),  # milliseconds
)
def test_interval_day_to_second_positive(days, hours, minutes, seconds, milliseconds):
    """IntervalDayToSecondMapper should correctly parse positive interval strings."""
    mapper = IntervalDayToSecondMapper()
    # Format as server would send: "D HH:MM:SS.mmm"
    interval_str = f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    result = mapper.map(interval_str)
    
    expected = timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds
    )
    assert result == expected


# Test 18: IntervalDayToSecondMapper negative intervals
@given(
    st.integers(min_value=0, max_value=999),  # days
    st.integers(min_value=0, max_value=23),   # hours
    st.integers(min_value=0, max_value=59),   # minutes
    st.integers(min_value=0, max_value=59),   # seconds
    st.integers(min_value=0, max_value=999),  # milliseconds
)
def test_interval_day_to_second_negative(days, hours, minutes, seconds, milliseconds):
    """IntervalDayToSecondMapper should correctly parse negative interval strings."""
    assume(days > 0 or hours > 0 or minutes > 0 or seconds > 0 or milliseconds > 0)
    
    mapper = IntervalDayToSecondMapper()
    # Format as server would send: "-D HH:MM:SS.mmm"
    interval_str = f"-{days} {hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    result = mapper.map(interval_str)
    
    expected = timedelta(
        days=-days,
        hours=-hours,
        minutes=-minutes,
        seconds=-seconds,
        milliseconds=-milliseconds
    )
    assert result == expected


# Test 19: StringValueMapper converts non-strings
@given(st.one_of(st.integers(), st.floats(allow_nan=False), st.booleans()))
def test_string_mapper_conversion(value):
    """StringValueMapper should convert any value to string."""
    mapper = StringValueMapper()
    result = mapper.map(value)
    assert result == str(value)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])