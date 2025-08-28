"""Property-based tests for trino.types module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
import pytest
import math

from trino.types import (
    Time, TimeWithTimeZone, Timestamp, TimestampWithTimeZone,
    NamedRowTuple, POWERS_OF_TEN, MAX_PYTHON_TEMPORAL_PRECISION_POWER
)
from trino.mapper import _fraction_to_decimal


# Strategy for reasonable fractional seconds (0 to 1 second in decimal)
fraction_strategy = st.decimals(
    min_value=Decimal('0'), 
    max_value=Decimal('0.999999999999'), 
    places=12
)

# Strategy for precision values
precision_strategy = st.integers(min_value=0, max_value=12)

# Strategy for time values
time_strategy = st.times()

# Strategy for datetime values  
datetime_strategy = st.datetimes(
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2100, 1, 1)
)

# Strategy for timezone-aware time values
timezone_strategy = st.sampled_from([
    timezone.utc,
    timezone(timedelta(hours=5, minutes=30)),
    timezone(timedelta(hours=-8)),
    timezone(timedelta(hours=12))
])

time_with_tz_strategy = st.builds(
    lambda t, tz: t.replace(tzinfo=tz),
    time_strategy,
    timezone_strategy
)

datetime_with_tz_strategy = st.builds(
    lambda dt, tz: dt.replace(tzinfo=tz),
    datetime_strategy,
    timezone_strategy
)


@given(
    whole_time=time_strategy,
    fraction=fraction_strategy,
    precision=precision_strategy
)
def test_time_round_to_precision_bounds(whole_time, fraction, precision):
    """Test that Time.round_to respects Python's microsecond precision limit."""
    time_obj = Time(whole_time, fraction)
    rounded = time_obj.round_to(precision)
    
    # The precision should be capped at MAX_PYTHON_TEMPORAL_PRECISION_POWER (6)
    effective_precision = min(precision, MAX_PYTHON_TEMPORAL_PRECISION_POWER)
    
    # After rounding, the fractional part should have at most effective_precision digits
    remaining = rounded._remaining_fractional_seconds
    
    # Check that the remaining fractional seconds are properly quantized
    if effective_precision < 12:
        quantization_factor = POWERS_OF_TEN[effective_precision]
        # The fractional part * quantization_factor should be close to an integer
        scaled = remaining * quantization_factor
        rounded_scaled = scaled.quantize(Decimal('1'))
        assert abs(scaled - rounded_scaled) < Decimal('0.5')


@given(
    whole_time=time_with_tz_strategy,
    fraction=fraction_strategy,
    delta_microseconds=st.integers(min_value=-86400000000, max_value=86400000000)
)
def test_time_add_time_delta_preserves_timezone(whole_time, fraction, delta_microseconds):
    """Test that Time.add_time_delta preserves timezone information."""
    time_obj = Time(whole_time, fraction)
    delta = timedelta(microseconds=delta_microseconds)
    
    # Skip if the delta would cause overflow
    try:
        result = time_obj.add_time_delta(delta)
    except (ValueError, OverflowError):
        assume(False)
    
    # The timezone should be preserved
    assert result.tzinfo == whole_time.tzinfo


@given(
    whole_time=time_with_tz_strategy,
    fraction=fraction_strategy,
    delta_microseconds=st.integers(min_value=-86400000000, max_value=86400000000)
)  
def test_timewithtz_add_time_delta_preserves_timezone(whole_time, fraction, delta_microseconds):
    """Test that TimeWithTimeZone.add_time_delta preserves timezone."""
    time_obj = TimeWithTimeZone(whole_time, fraction)
    delta = timedelta(microseconds=delta_microseconds)
    
    try:
        result = time_obj.add_time_delta(delta)
    except (ValueError, OverflowError):
        assume(False)
    
    # The timezone should be preserved
    assert result.tzinfo == whole_time.tzinfo


@given(
    whole_datetime=datetime_strategy,
    fraction=fraction_strategy,
    precision=precision_strategy
)
def test_timestamp_round_to_precision_bounds(whole_datetime, fraction, precision):
    """Test that Timestamp.round_to respects Python's microsecond precision limit."""
    ts_obj = Timestamp(whole_datetime, fraction)
    rounded = ts_obj.round_to(precision)
    
    # The precision should be capped at MAX_PYTHON_TEMPORAL_PRECISION_POWER (6)
    effective_precision = min(precision, MAX_PYTHON_TEMPORAL_PRECISION_POWER)
    
    # After rounding, the fractional part should have at most effective_precision digits
    remaining = rounded._remaining_fractional_seconds
    
    # Check that the remaining fractional seconds are properly quantized
    if effective_precision < 12:
        quantization_factor = POWERS_OF_TEN[effective_precision]
        scaled = remaining * quantization_factor
        rounded_scaled = scaled.quantize(Decimal('1'))
        assert abs(scaled - rounded_scaled) < Decimal('0.5')


@given(
    whole_datetime=datetime_with_tz_strategy,
    fraction=fraction_strategy,
    delta_seconds=st.integers(min_value=-86400, max_value=86400)
)
def test_timestampwithtz_add_time_delta_preserves_timezone(whole_datetime, fraction, delta_seconds):
    """Test that TimestampWithTimeZone.add_time_delta preserves timezone."""
    ts_obj = TimestampWithTimeZone(whole_datetime, fraction)
    delta = timedelta(seconds=delta_seconds)
    
    result = ts_obj.add_time_delta(delta)
    
    # The timezone should be preserved
    assert result.tzinfo == whole_datetime.tzinfo


# Strategy for valid Python identifiers (for NamedRowTuple field names)
name_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_',
        min_size=1,
        max_size=20
    ).filter(lambda s: s.isidentifier())
)

value_strategy = st.one_of(
    st.none(),
    st.integers(),
    st.text(max_size=10),
    st.floats(allow_nan=False, allow_infinity=False)
)


@given(
    values=st.lists(value_strategy, min_size=1, max_size=10),
    names=st.lists(name_strategy, min_size=1, max_size=10),
    types=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10)
)
def test_namedrowtuple_unique_name_access(values, names, types):
    """Test that NamedRowTuple allows access to unique names as attributes."""
    # Make lists same length
    min_len = min(len(values), len(names), len(types))
    values = values[:min_len]
    names = names[:min_len]
    types = types[:min_len]
    
    row = NamedRowTuple(values, names, types)
    
    # Check that unique non-None names can be accessed as attributes
    for i, name in enumerate(names):
        if name is not None and names.count(name) == 1:
            assert hasattr(row, name)
            assert getattr(row, name) == values[i]


@given(
    values=st.lists(value_strategy, min_size=2, max_size=10),
    name=name_strategy.filter(lambda n: n is not None),
    types=st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10)
)
def test_namedrowtuple_duplicate_name_raises_error(values, name, types):
    """Test that accessing duplicate names in NamedRowTuple raises ValueError."""
    # Create names list with duplicates
    min_len = min(len(values), len(types))
    values = values[:min_len]
    types = types[:min_len]
    names = [name] * min_len  # All names are the same
    
    row = NamedRowTuple(values, names, types)
    
    # Accessing a duplicate name should raise ValueError
    with pytest.raises(ValueError, match="Ambiguous row field reference"):
        getattr(row, name)


@given(
    values=st.lists(value_strategy, min_size=1, max_size=10),
    names=st.lists(name_strategy, min_size=1, max_size=10),
    types=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10)
)
def test_namedrowtuple_is_tuple(values, names, types):
    """Test that NamedRowTuple behaves as a tuple."""
    # Make lists same length
    min_len = min(len(values), len(names), len(types))
    values = values[:min_len]
    names = names[:min_len]
    types = types[:min_len]
    
    row = NamedRowTuple(values, names, types)
    
    # Should be a tuple
    assert isinstance(row, tuple)
    
    # Should have same length as values
    assert len(row) == len(values)
    
    # Should be indexable
    for i, value in enumerate(values):
        assert row[i] == value


@given(
    fractional_str=st.text(
        alphabet='0123456789',
        min_size=0,
        max_size=12
    )
)
def test_fraction_to_decimal_basic(fractional_str):
    """Test _fraction_to_decimal converts fractional strings correctly."""
    result = _fraction_to_decimal(fractional_str)
    
    if fractional_str == '':
        assert result == Decimal(0)
    else:
        # The result should be the fractional part divided by the appropriate power of 10
        expected = Decimal(fractional_str) / POWERS_OF_TEN[len(fractional_str)]
        assert result == expected


@given(
    fractional_str=st.text(
        alphabet='0123456789',
        min_size=1,
        max_size=12
    )
)
def test_fraction_to_decimal_range(fractional_str):
    """Test that _fraction_to_decimal produces values in [0, 1) range."""
    result = _fraction_to_decimal(fractional_str)
    
    # Result should be in [0, 1) range for valid fractional parts
    assert Decimal(0) <= result < Decimal(1)


@given(
    whole_time=time_strategy,
    fraction=fraction_strategy,
    precision=precision_strategy
)  
def test_time_round_to_idempotent(whole_time, fraction, precision):
    """Test that rounding to the same precision twice gives same result (idempotence)."""
    time_obj = Time(whole_time, fraction)
    rounded_once = time_obj.round_to(precision)
    rounded_twice = rounded_once.round_to(precision)
    
    # Rounding twice to same precision should give same result
    assert rounded_once._whole_python_temporal_value == rounded_twice._whole_python_temporal_value
    assert rounded_once._remaining_fractional_seconds == rounded_twice._remaining_fractional_seconds


@given(
    whole_time=time_strategy,
    fraction=fraction_strategy
)
def test_time_to_python_type_with_zero_fraction(whole_time, fraction):
    """Test Time.to_python_type when fraction is zero."""
    time_obj = Time(whole_time, Decimal(0))
    result = time_obj.to_python_type()
    
    # Should return the whole time unchanged when fraction is 0
    assert result == whole_time


@given(
    whole_datetime=datetime_strategy,
    fraction=fraction_strategy
)
def test_timestamp_to_python_type_with_zero_fraction(whole_datetime, fraction):
    """Test Timestamp.to_python_type when fraction is zero."""
    ts_obj = Timestamp(whole_datetime, Decimal(0))
    result = ts_obj.to_python_type()
    
    # Should return the whole datetime unchanged when fraction is 0
    assert result == whole_datetime