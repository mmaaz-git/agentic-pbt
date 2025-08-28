"""Investigation tests to find potential bugs in trino.types."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings, example
import pytest

from trino.types import (
    Time, TimeWithTimeZone, Timestamp, TimestampWithTimeZone,
    NamedRowTuple, POWERS_OF_TEN, MAX_PYTHON_TEMPORAL_PRECISION_POWER
)
from trino.mapper import _fraction_to_decimal


# Test for potential overflow in time arithmetic
@given(
    # Choose a time very close to midnight
    whole_time=st.times(
        min_value=time(23, 59, 59, 999999),
        max_value=time(23, 59, 59, 999999)
    ),
    # Add any fractional seconds
    fraction=st.decimals(
        min_value=Decimal('0.000001'),
        max_value=Decimal('0.999999'),
        places=6
    )
)
def test_time_overflow_at_midnight(whole_time, fraction):
    """Test Time operations near midnight boundary."""
    time_obj = Time(whole_time, fraction)
    
    # When converting to Python type with additional microseconds
    result = time_obj.to_python_type()
    
    # The result should handle day wraparound correctly
    # If it overflows past 23:59:59.999999, it should wrap to next day
    assert isinstance(result, time)
    # Time objects don't have dates, so they should wrap around
    # This might reveal if there's improper handling


# Test for metamorphic property: round_to with different precisions
@given(
    whole_time=st.times(),
    fraction=st.decimals(
        min_value=Decimal('0'),
        max_value=Decimal('0.999999999999'),
        places=12
    ),
    precision1=st.integers(min_value=0, max_value=6),
    precision2=st.integers(min_value=0, max_value=6)
)
def test_time_round_to_ordering(whole_time, fraction, precision1, precision2):
    """Test that higher precision preserves more information."""
    time_obj = Time(whole_time, fraction)
    
    rounded1 = time_obj.round_to(precision1)
    rounded2 = time_obj.round_to(precision2)
    
    # If precision1 <= precision2, then rounding to precision1 loses more info
    if precision1 <= precision2:
        # Rounding the more precise one to less precise should give same result
        rounded2_then_1 = rounded2.round_to(precision1)
        assert rounded1._remaining_fractional_seconds == rounded2_then_1._remaining_fractional_seconds


# Test potential issue with _fraction_to_decimal when string is "0"
def test_fraction_to_decimal_single_zero():
    """Test _fraction_to_decimal with single '0'."""
    result = _fraction_to_decimal("0")
    # "0" with length 1 should give 0/10 = 0
    assert result == Decimal(0)


# Test potential issue with large fractions in _fraction_to_decimal
@given(
    # Generate strings of 9s (maximum fractional value)
    length=st.integers(min_value=1, max_value=12)
)
def test_fraction_to_decimal_max_values(length):
    """Test _fraction_to_decimal with maximum fractional values."""
    fractional_str = "9" * length
    result = _fraction_to_decimal(fractional_str)
    
    # Should be just under 1
    assert result < Decimal(1)
    # Should be close to 1 for longer strings
    if length >= 6:
        assert result > Decimal('0.99')


# Test NamedRowTuple.__getattr__ edge case
def test_namedrowtuple_getattr_with_count_method():
    """Test that 'count' method name in fields doesn't break."""
    # 'count' is a tuple method - might cause issues
    values = [1, 2, 3]
    names = ["count", "field2", "field3"]
    types = ["int", "int", "int"]
    
    row = NamedRowTuple(values, names, types)
    
    # The attribute 'count' should return the value, not the tuple method
    assert row.count == 1  # Should be the value, not the method
    
    # But tuple's count method should still work
    assert row.count(1) == 1  # Counts occurrences of value 1


# Test NamedRowTuple with reserved Python keywords
@given(
    keyword=st.sampled_from(['class', 'def', 'return', 'if', 'else', 'for', 'while', 'import', 'from', 'as'])
)
def test_namedrowtuple_with_python_keywords(keyword):
    """Test NamedRowTuple with Python keywords as field names."""
    values = [42, 100, 200]
    names = [keyword, "field2", "field3"]
    types = ["int", "int", "int"]
    
    row = NamedRowTuple(values, names, types)
    
    # Should be able to access even with keyword names
    assert getattr(row, keyword) == 42


# Test Time operations with NaN or Inf in Decimal
def test_time_with_nan_fraction():
    """Test Time with NaN fractional seconds."""
    whole_time = time(12, 0, 0)
    
    # Decimal can represent NaN
    nan_fraction = Decimal('NaN')
    
    time_obj = Time(whole_time, nan_fraction)
    
    # This might cause issues in round_to due to as_tuple().exponent
    try:
        rounded = time_obj.round_to(3)
        # If it doesn't error, check the result
        assert rounded._remaining_fractional_seconds.is_nan()
    except:
        # This would be a bug - NaN should be handled
        assert False, "round_to should handle NaN fractions"


def test_time_with_inf_fraction():
    """Test Time with Inf fractional seconds."""
    whole_time = time(12, 0, 0)
    
    # Decimal can represent Infinity
    inf_fraction = Decimal('Infinity')
    
    time_obj = Time(whole_time, inf_fraction)
    
    # This might cause issues in round_to or to_python_type
    try:
        result = time_obj.to_python_type()
        # If it doesn't error, it's handling infinity somehow
        # This is likely a bug as infinity seconds doesn't make sense
        assert False, "Should not accept infinite fractional seconds"
    except (ValueError, OverflowError, TypeError):
        # Expected - infinity should cause an error
        pass


# Test the specific case of round_to when exponent is not a simple negative number
def test_time_round_to_with_special_decimal():
    """Test round_to with special Decimal values."""
    whole_time = time(12, 0, 0)
    
    # Create a Decimal with exponent that's not a simple negative integer
    # Decimal('1E+2') has positive exponent
    special_fraction = Decimal('0.1E-5')  # = 0.000001
    
    time_obj = Time(whole_time, special_fraction)
    rounded = time_obj.round_to(3)
    
    # Should handle scientific notation correctly
    assert rounded._remaining_fractional_seconds == Decimal('0')


# Test for potential integer overflow in microseconds calculation
@given(
    whole_time=st.times(),
    # Use maximum possible fraction just under 1 second
    fraction=st.just(Decimal('0.999999999999'))
)
def test_time_microsecond_overflow(whole_time, fraction):
    """Test potential overflow in microseconds calculation."""
    time_obj = Time(whole_time, fraction)
    
    # to_python_type multiplies by MAX_PYTHON_TEMPORAL_PRECISION (10^6)
    result = time_obj.to_python_type()
    
    # Should not overflow or lose precision catastrophically
    assert isinstance(result, time)


# Test round_to with negative precision
@given(
    whole_time=st.times(),
    fraction=st.decimals(min_value=Decimal('0'), max_value=Decimal('0.999999'), places=6),
    negative_precision=st.integers(min_value=-10, max_value=-1)
)
def test_time_round_to_negative_precision(whole_time, fraction, negative_precision):
    """Test round_to with negative precision values."""
    time_obj = Time(whole_time, fraction)
    
    # What happens with negative precision?
    rounded = time_obj.round_to(negative_precision)
    
    # Negative precision gets capped at 0 by min(precision, MAX_PYTHON_TEMPORAL_PRECISION_POWER)
    # Since MAX_PYTHON_TEMPORAL_PRECISION_POWER = 6, min(negative, 6) = negative
    # Then in the check digits > precision, with negative precision, this is always true
    # This might cause unexpected behavior
    assert isinstance(rounded.to_python_type(), time)