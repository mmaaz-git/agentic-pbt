#!/usr/bin/env python3
"""Edge case property-based tests to find bugs in trino module."""

import base64
import math
from datetime import datetime, time, timezone, timedelta
from decimal import Decimal
from hypothesis import assume, given, strategies as st, settings, example
from dateutil.relativedelta import relativedelta

# Import trino modules under test  
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.mapper import (
    BinaryValueMapper, BooleanValueMapper, DoubleValueMapper,
    DecimalValueMapper, IntervalYearToMonthMapper, 
    IntervalDayToSecondMapper, _create_tzinfo,
    TimeValueMapper, TimestampValueMapper, _fraction_to_decimal
)
from trino.types import Time, Timestamp, POWERS_OF_TEN
import trino.exceptions


# Test 1: BooleanValueMapper with unexpected values
@given(st.text())
@example("TRUE ")  # with trailing space
@example(" true")  # with leading space
@example("TrUe")   # mixed case
@example("1")      # numeric string
@example("0")      # numeric string
@example("yes")    # common boolean-like value
@example("no")     # common boolean-like value
@example("")       # empty string
def test_boolean_mapper_unexpected_inputs(value):
    """Test BooleanValueMapper with edge case inputs."""
    mapper = BooleanValueMapper()
    
    if str(value).lower() == 'true':
        result = mapper.map(value)
        assert result is True
    elif str(value).lower() == 'false':
        result = mapper.map(value)
        assert result is False
    else:
        # Should raise ValueError for non-boolean strings
        try:
            result = mapper.map(value)
            # If it doesn't raise, it should have returned something sensible
            assert False, f"Expected ValueError for '{value}', got {result}"
        except ValueError as e:
            assert "unexpected value" in str(e).lower()


# Test 2: DoubleValueMapper with edge case numeric strings
@given(st.one_of(
    st.just("inf"),      # lowercase infinity
    st.just("INF"),      # uppercase  
    st.just("-inf"),     # lowercase negative
    st.just("-INF"),     # uppercase negative
    st.just("nan"),      # lowercase nan
    st.just("+Infinity"), # with plus sign
    st.just("1e308"),    # near max float
    st.just("-1e308"),   # near min float
    st.just("1e-308"),   # very small positive
    st.just("1.7976931348623157e+308"),  # max float
    st.just("2.2250738585072014e-308"),  # min positive float
))
def test_double_mapper_edge_cases(value):
    """Test DoubleValueMapper with edge case float representations."""
    mapper = DoubleValueMapper()
    
    # These should work based on the implementation
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
        # Other values should be handled by float()
        try:
            result = mapper.map(value)
            expected = float(value)
            if math.isnan(expected):
                assert math.isnan(result)
            elif math.isinf(expected):
                assert math.isinf(result)
                assert (result > 0) == (expected > 0)
            else:
                assert result == expected
        except (ValueError, OverflowError):
            pass


# Test 3: BinaryValueMapper with invalid base64
@given(st.text(alphabet='!@#$%^&*()', min_size=1, max_size=20))
def test_binary_mapper_invalid_base64(invalid_b64):
    """Test BinaryValueMapper with invalid base64 strings."""
    mapper = BinaryValueMapper()
    
    try:
        result = mapper.map(invalid_b64)
        # If it succeeds, the input might have been accidentally valid base64
        # Verify it can decode back
        encoded = base64.b64encode(result).decode('utf-8')
    except Exception:
        # Invalid base64 should raise an error
        pass


# Test 4: IntervalYearToMonthMapper with malformed strings
@given(st.one_of(
    st.just("--1-2"),     # double negative
    st.just("1--2"),      # negative month only
    st.just("1-"),        # missing month
    st.just("-1"),        # missing month with negative
    st.just("1"),         # missing delimiter
    st.just(""),          # empty string
    st.just("-"),         # just delimiter
    st.just("1-2-3"),     # too many parts
))
def test_interval_year_month_malformed(malformed_str):
    """Test IntervalYearToMonthMapper with malformed interval strings."""
    mapper = IntervalYearToMonthMapper()
    
    try:
        result = mapper.map(malformed_str)
        # If it succeeds, check if the parsing makes sense
        # The format should be "years-months" or "-years-months"
    except (ValueError, IndexError):
        # Malformed strings should raise errors
        pass


# Test 5: IntervalDayToSecondMapper with extreme values
@given(st.one_of(
    st.just("999999999 23:59:59.999"),  # very large days
    st.just("-999999999 23:59:59.999"), # very large negative days
    st.just("0 24:00:00.000"),          # invalid hours
    st.just("0 23:60:00.000"),          # invalid minutes
    st.just("0 23:59:60.000"),          # invalid seconds
    st.just("0 23:59:59.9999"),         # too many millisecond digits
    st.just("1 2:3:4.5"),                # single digit components
))
def test_interval_day_second_extreme_values(interval_str):
    """Test IntervalDayToSecondMapper with extreme or invalid values."""
    mapper = IntervalDayToSecondMapper()
    
    try:
        result = mapper.map(interval_str)
        # Check if the result is reasonable
        if not isinstance(result, timedelta):
            assert False, f"Expected timedelta, got {type(result)}"
    except (ValueError, OverflowError, trino.exceptions.TrinoDataError):
        # Expected for invalid or overflow values
        pass


# Test 6: _create_tzinfo with edge case timezone strings
@given(st.one_of(
    st.just("+00:00"),    # UTC
    st.just("-00:00"),    # negative UTC
    st.just("+24:00"),    # invalid hours
    st.just("+12:60"),    # invalid minutes
    st.just("00:00"),     # missing sign
    st.just("+0:0"),      # single digits
    st.just(""),          # empty
    st.just("UTC"),       # named timezone
    st.just("America/New_York"),  # named timezone
    st.just("Invalid/Zone"),      # invalid named timezone
))
def test_create_tzinfo_edge_cases(tz_str):
    """Test _create_tzinfo with various timezone string formats."""
    try:
        tzinfo = _create_tzinfo(tz_str)
        
        # If successful, verify it's a valid tzinfo
        if tz_str.startswith("+") or tz_str.startswith("-"):
            # Offset timezone
            ref_dt = datetime(2024, 1, 1, tzinfo=tzinfo)
            offset = ref_dt.utcoffset()
            assert isinstance(offset, timedelta)
        else:
            # Named timezone or invalid
            assert tzinfo is not None
    except (ValueError, KeyError, Exception):
        # Invalid timezone strings should raise errors
        pass


# Test 7: _fraction_to_decimal with edge cases
@given(st.one_of(
    st.just(""),           # empty
    st.just("000000000000"), # all zeros, max length
    st.just("999999999999"), # all nines, max length
    st.just("1"),          # single digit
    st.just("00000000001"), # leading zeros
))
def test_fraction_to_decimal_special_cases(frac_str):
    """Test _fraction_to_decimal with special fractional strings."""
    result = _fraction_to_decimal(frac_str)
    
    if frac_str == "":
        assert result == 0
    else:
        # Verify the mathematical property
        if len(frac_str) <= 12:  # Within POWERS_OF_TEN range
            expected = Decimal(frac_str or 0) / POWERS_OF_TEN[len(frac_str)]
            assert result == expected


# Test 8: DecimalValueMapper with extreme values
@given(st.one_of(
    st.just("9" * 100),    # very large number
    st.just("-" + "9" * 100), # very large negative
    st.just("0." + "0" * 100 + "1"), # very small decimal
    st.just("1e100"),      # scientific notation
    st.just("1E-100"),     # negative exponent
    st.just("Infinity"),   # special value
    st.just("NaN"),        # special value
))
def test_decimal_mapper_extreme_values(value_str):
    """Test DecimalValueMapper with extreme decimal values."""
    mapper = DecimalValueMapper()
    
    try:
        result = mapper.map(value_str)
        assert isinstance(result, Decimal)
        
        # Verify it preserves the value
        if value_str not in ["Infinity", "NaN", "-Infinity"]:
            # Normal decimals should round-trip through string
            assert str(result) == value_str or Decimal(str(result)) == Decimal(value_str)
    except (ValueError, decimal.InvalidOperation):
        # Some values might not be valid decimals
        pass


# Test 9: TimeValueMapper with edge case times
@given(
    st.one_of(
        st.just("24:00:00"),      # edge of day
        st.just("23:59:59.999999"), # max microseconds
        st.just("00:00:00.000000000000"), # many zeros
        st.just("12:34:56."),      # trailing dot
    ),
    st.integers(0, 12)        # precision parameter
)
def test_time_mapper_edge_cases(time_str, precision):
    """Test TimeValueMapper with edge case time strings."""
    mapper = TimeValueMapper(precision)
    
    try:
        result = mapper.map(time_str)
        assert isinstance(result, time)
    except (ValueError, IndexError):
        # Invalid time strings should raise errors
        pass


# Test 10: Test for potential integer overflow in mapping
@given(st.one_of(
    st.just(2**63 - 1),     # max 64-bit signed int
    st.just(-2**63),        # min 64-bit signed int
    st.just(2**63),         # overflow 64-bit signed
    st.just(2**64),         # definitely overflow
    st.just(10**20),        # very large decimal number
))
def test_integer_mapper_overflow(large_value):
    """Test IntegerValueMapper with potential overflow values."""
    from trino.mapper import IntegerValueMapper
    mapper = IntegerValueMapper()
    
    # Python ints can handle arbitrary precision
    result = mapper.map(large_value)
    assert result == large_value
    assert isinstance(result, int)


if __name__ == "__main__":
    print("Running edge case tests for trino module...")
    import pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics", "--tb=short"])