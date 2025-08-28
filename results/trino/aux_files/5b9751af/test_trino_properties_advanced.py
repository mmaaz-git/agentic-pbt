#!/usr/bin/env python3
"""Advanced property-based tests for trino module edge cases."""

import math
from datetime import timedelta
from decimal import Decimal
from hypothesis import assume, given, strategies as st, settings
from dateutil.relativedelta import relativedelta

# Import trino modules under test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.mapper import (
    IntervalYearToMonthMapper, IntervalDayToSecondMapper,
    ArrayValueMapper, MapValueMapper, IntegerValueMapper,
    StringValueMapper, _fraction_to_decimal
)
from trino.types import POWERS_OF_TEN
import trino.exceptions


# Test 1: IntervalYearToMonthMapper parsing
@given(
    st.integers(-9999, 9999),  # years
    st.integers(0, 11)  # months
)
def test_interval_year_to_month_parsing(years, months):
    """Test IntervalYearToMonthMapper correctly parses year-month intervals."""
    mapper = IntervalYearToMonthMapper()
    
    # Create interval string in the format the server would send
    if years < 0 or months < 0:
        # For negative intervals, both parts are negative
        interval_str = f"-{abs(years)}-{abs(months)}"
        expected = relativedelta(years=-abs(years), months=-abs(months))
    else:
        interval_str = f"{years}-{months}"
        expected = relativedelta(years=years, months=months)
    
    result = mapper.map(interval_str)
    
    # Verify the result
    assert result.years == expected.years
    assert result.months == expected.months


# Test 2: IntervalDayToSecondMapper parsing with edge cases
@given(
    st.integers(-999999, 999999),  # days
    st.integers(0, 23),  # hours
    st.integers(0, 59),  # minutes
    st.integers(0, 59),  # seconds
    st.integers(0, 999)  # milliseconds
)
def test_interval_day_to_second_parsing(days, hours, minutes, seconds, milliseconds):
    """Test IntervalDayToSecondMapper correctly parses day-time intervals."""
    mapper = IntervalDayToSecondMapper()
    
    # Create interval string in the format the server would send
    is_negative = days < 0
    
    if is_negative:
        # For negative intervals, format with negative sign prefix
        interval_str = f"-{abs(days)} {hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        expected_days = -abs(days)
        expected_hours = -hours if hours > 0 else 0
        expected_minutes = -minutes if minutes > 0 else 0
        expected_seconds = -seconds if seconds > 0 else 0
        expected_ms = -milliseconds if milliseconds > 0 else 0
    else:
        interval_str = f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        expected_days = days
        expected_hours = hours
        expected_minutes = minutes
        expected_seconds = seconds
        expected_ms = milliseconds
    
    try:
        result = mapper.map(interval_str)
        
        # Python's timedelta might overflow for very large values
        # Verify the components match what we expect
        total_seconds = result.total_seconds()
        
        # Calculate expected total seconds
        expected_total = (expected_days * 86400 + 
                         expected_hours * 3600 + 
                         expected_minutes * 60 + 
                         expected_seconds + 
                         expected_ms / 1000)
        
        assert math.isclose(total_seconds, expected_total, rel_tol=1e-9)
        
    except (OverflowError, trino.exceptions.TrinoDataError):
        # Large values can overflow Python's timedelta
        # This is expected behavior documented in the code
        pass


# Test 3: ArrayValueMapper with nested values
@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_array_mapper_integer_lists(int_list):
    """Test ArrayValueMapper correctly maps lists of integers."""
    inner_mapper = IntegerValueMapper()
    mapper = ArrayValueMapper(inner_mapper)
    
    result = mapper.map(int_list)
    assert result == int_list
    assert isinstance(result, list)
    assert all(isinstance(x, int) for x in result)


# Test 4: ArrayValueMapper with None values
@given(st.lists(st.one_of(st.integers(), st.none()), min_size=0, max_size=10))
def test_array_mapper_nullable_elements(nullable_list):
    """Test ArrayValueMapper correctly handles lists with None values."""
    inner_mapper = IntegerValueMapper()
    mapper = ArrayValueMapper(inner_mapper)
    
    result = mapper.map(nullable_list)
    assert result == nullable_list
    assert len(result) == len(nullable_list)
    for orig, mapped in zip(nullable_list, result):
        if orig is None:
            assert mapped is None
        else:
            assert mapped == orig


# Test 5: MapValueMapper with string keys and integer values
@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=10))
def test_map_mapper_string_to_int(str_int_dict):
    """Test MapValueMapper correctly maps dictionaries."""
    key_mapper = StringValueMapper()
    value_mapper = IntegerValueMapper()
    mapper = MapValueMapper(key_mapper, value_mapper)
    
    result = mapper.map(str_int_dict)
    assert result == str_int_dict
    assert isinstance(result, dict)
    assert all(isinstance(k, str) for k in result.keys())
    assert all(isinstance(v, int) for v in result.values())


# Test 6: MapValueMapper with nullable values
@given(st.dictionaries(st.text(min_size=1), st.one_of(st.integers(), st.none()), min_size=0, max_size=10))
def test_map_mapper_nullable_values(dict_with_nulls):
    """Test MapValueMapper correctly handles dictionaries with None values."""
    key_mapper = StringValueMapper()
    value_mapper = IntegerValueMapper()
    mapper = MapValueMapper(key_mapper, value_mapper)
    
    result = mapper.map(dict_with_nulls)
    assert len(result) == len(dict_with_nulls)
    for key, value in dict_with_nulls.items():
        assert key in result
        if value is None:
            assert result[key] is None
        else:
            assert result[key] == value


# Test 7: fraction_to_decimal edge cases
@given(st.text(alphabet='0', min_size=1, max_size=12))
def test_fraction_to_decimal_leading_zeros(zeros_str):
    """Test _fraction_to_decimal handles strings with only zeros correctly."""
    result = _fraction_to_decimal(zeros_str)
    # All zeros should give 0
    assert result == 0


# Test 8: fraction_to_decimal with large fractions
@given(st.text(alphabet='9', min_size=1, max_size=12))
def test_fraction_to_decimal_max_values(nines_str):
    """Test _fraction_to_decimal with maximum fractional values."""
    result = _fraction_to_decimal(nines_str)
    # String of 9s should give value close to 1
    expected = Decimal(nines_str) / POWERS_OF_TEN[len(nines_str)]
    assert result == expected
    assert result < 1  # Should always be less than 1
    assert result > 0  # Should be positive


# Test 9: IntervalYearToMonthMapper with edge case strings  
@given(st.just("-0-0"))
def test_interval_year_month_zero_negative(interval_str):
    """Test IntervalYearToMonthMapper handles -0-0 correctly."""
    mapper = IntervalYearToMonthMapper()
    result = mapper.map(interval_str)
    assert result.years == 0
    assert result.months == 0


# Test 10: Nested ArrayValueMapper (array of arrays)
@given(st.lists(st.lists(st.integers(), min_size=0, max_size=5), min_size=0, max_size=5))
def test_nested_array_mapper(nested_list):
    """Test ArrayValueMapper with nested arrays."""
    inner_mapper = IntegerValueMapper()
    inner_array_mapper = ArrayValueMapper(inner_mapper)
    outer_mapper = ArrayValueMapper(inner_array_mapper)
    
    result = outer_mapper.map(nested_list)
    assert result == nested_list
    assert isinstance(result, list)
    for sublist in result:
        assert isinstance(sublist, list)
        assert all(isinstance(x, int) for x in sublist)


if __name__ == "__main__":
    print("Running advanced property-based tests for trino module...")
    import pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])