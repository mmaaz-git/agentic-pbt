"""Additional property-based tests for trino.types focusing on edge cases."""

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


# Test for very large fractional values close to 1 second
@given(
    whole_time=st.times(),
    # Generate fractions very close to 1 second
    fraction=st.decimals(
        min_value=Decimal('0.999999999999'),
        max_value=Decimal('0.999999999999'),
        places=12
    ),
    precision=st.integers(min_value=0, max_value=6)
)
def test_time_round_to_with_near_one_second_fraction(whole_time, fraction, precision):
    """Test rounding behavior when fraction is very close to 1 second."""
    time_obj = Time(whole_time, fraction)
    rounded = time_obj.round_to(precision)
    result = rounded.to_python_type()
    
    # When rounding a fraction very close to 1, it might round up to the next second
    # This should be handled correctly without overflow
    assert isinstance(result, time)


@given(
    whole_datetime=st.datetimes(
        min_value=datetime(2000, 1, 1, 23, 59, 59),
        max_value=datetime(2000, 1, 1, 23, 59, 59)
    ),
    # Fraction that when rounded might add a second
    fraction=st.decimals(
        min_value=Decimal('0.999999'),
        max_value=Decimal('0.999999999999'),
        places=12
    ),
    precision=st.integers(min_value=0, max_value=2)
)
def test_timestamp_round_to_at_day_boundary(whole_datetime, fraction, precision):
    """Test timestamp rounding at day boundaries."""
    ts_obj = Timestamp(whole_datetime, fraction)
    rounded = ts_obj.round_to(precision)
    result = rounded.to_python_type()
    
    # The result should still be a valid datetime
    assert isinstance(result, datetime)


# Test the __getattr__ behavior for non-existent duplicate names
@given(
    values=st.lists(st.integers(), min_size=2, max_size=5),
    types=st.lists(st.text(min_size=1, max_size=5), min_size=2, max_size=5)
)
def test_namedrowtuple_getattr_nonexistent_duplicate(values, types):
    """Test __getattr__ raises ValueError for any name that appears more than once."""
    min_len = min(len(values), len(types))
    values = values[:min_len]
    types = types[:min_len]
    
    # Create a list with duplicate "field1" and "field2"
    names = ["field1", "field1"] + ["field2"] * (min_len - 2) if min_len > 2 else ["field1", "field1"]
    
    row = NamedRowTuple(values, names, types)
    
    # Even accessing a non-existent name that would be duplicate should raise ValueError
    # if count > 0
    with pytest.raises(ValueError, match="Ambiguous row field reference"):
        getattr(row, "field1")


# Test empty fractional string
def test_fraction_to_decimal_empty_string():
    """Test _fraction_to_decimal with empty string."""
    result = _fraction_to_decimal("")
    assert result == Decimal(0)


# Test leading zeros in fractional part
@given(
    num_zeros=st.integers(min_value=1, max_value=5),
    digits=st.text(alphabet='123456789', min_size=1, max_size=5)
)
def test_fraction_to_decimal_leading_zeros(num_zeros, digits):
    """Test _fraction_to_decimal preserves leading zeros significance."""
    fractional_str = "0" * num_zeros + digits
    result = _fraction_to_decimal(fractional_str)
    
    # Leading zeros matter for the denominator
    expected = Decimal(fractional_str) / POWERS_OF_TEN[len(fractional_str)]
    assert result == expected
    
    # Result should be smaller due to leading zeros
    assert result < Decimal("0.1")


# Test the Time.new_instance method
@given(
    time1=st.times(),
    time2=st.times(),
    fraction1=st.decimals(min_value=Decimal('0'), max_value=Decimal('0.999999'), places=6),
    fraction2=st.decimals(min_value=Decimal('0'), max_value=Decimal('0.999999'), places=6)
)
def test_time_new_instance_creates_new_object(time1, time2, fraction1, fraction2):
    """Test that new_instance creates a new Time object correctly."""
    time_obj = Time(time1, fraction1)
    new_obj = time_obj.new_instance(time2, fraction2)
    
    assert isinstance(new_obj, Time)
    assert new_obj._whole_python_temporal_value == time2
    assert new_obj._remaining_fractional_seconds == fraction2
    # Should be different objects
    assert new_obj is not time_obj


# Test round_to with precision = 0  
@given(
    whole_time=st.times(),
    fraction=st.decimals(min_value=Decimal('0.1'), max_value=Decimal('0.999999'), places=6)
)
def test_time_round_to_zero_precision(whole_time, fraction):
    """Test rounding to 0 precision (whole seconds)."""
    time_obj = Time(whole_time, fraction)
    rounded = time_obj.round_to(0)
    
    # With 0 precision, fractional part should round to 0 or 1
    remaining = rounded._remaining_fractional_seconds
    assert remaining == Decimal(0) or remaining == Decimal(1)


# Test very precise fractions
@given(
    whole_time=st.times(),
    # Generate very precise decimal values
    fraction=st.decimals(min_value=Decimal('0'), max_value=Decimal('0.999999999999'), places=12)
)
def test_time_high_precision_fraction_handling(whole_time, fraction):
    """Test handling of high-precision fractional seconds."""
    time_obj = Time(whole_time, fraction)
    
    # to_python_type should handle high precision gracefully
    result = time_obj.to_python_type()
    assert isinstance(result, time)
    
    # Python time only supports microseconds, so we lose precision beyond 6 decimal places
    if fraction > 0:
        # The conversion should work without error
        time_delta = timedelta(microseconds=int(fraction * POWERS_OF_TEN[6]))
        expected = time_obj.add_time_delta(time_delta)
        # Can't directly compare due to precision loss, but both should be valid times
        assert isinstance(expected, time)


# Test NamedRowTuple with None values
@given(
    num_items=st.integers(min_value=1, max_value=5)
)  
def test_namedrowtuple_with_all_none_names(num_items):
    """Test NamedRowTuple when all names are None."""
    values = list(range(num_items))
    names = [None] * num_items
    types = [f"type{i}" for i in range(num_items)]
    
    row = NamedRowTuple(values, names, types)
    
    # Should still work as a tuple
    assert len(row) == num_items
    for i in range(num_items):
        assert row[i] == values[i]
    
    # No attributes should be set
    for i in range(num_items):
        assert not hasattr(row, f"field{i}")


# Test the annotations
@given(
    values=st.lists(st.integers(), min_size=1, max_size=5),
    names=st.lists(st.one_of(st.none(), st.text(min_size=1, max_size=5)), min_size=1, max_size=5),
    types=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=5)
)
def test_namedrowtuple_annotations(values, names, types):
    """Test that NamedRowTuple properly sets annotations."""
    min_len = min(len(values), len(names), len(types))
    values = values[:min_len]
    names = names[:min_len]
    types = types[:min_len]
    
    row = NamedRowTuple(values, names, types)
    
    # Check annotations are set correctly
    assert hasattr(row, '__annotations__')
    assert row.__annotations__['names'] == names
    assert row.__annotations__['types'] == types


# Test __getnewargs__ and pickle support
@given(
    values=st.lists(st.integers(), min_size=1, max_size=3),
    names=st.lists(st.one_of(st.none(), st.text(min_size=1, max_size=3)), min_size=1, max_size=3),
    types=st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=3)
)
def test_namedrowtuple_getnewargs(values, names, types):
    """Test __getnewargs__ for pickling support."""
    min_len = min(len(values), len(names), len(types))
    values = values[:min_len]
    names = names[:min_len]
    types = types[:min_len]
    
    row = NamedRowTuple(values, names, types)
    new_args = row.__getnewargs__()
    
    # Should return (tuple(self), (), ())
    assert new_args == (tuple(row), (), ())


# Test state preservation
@given(
    values=st.lists(st.integers(), min_size=1, max_size=3),
    names=st.lists(st.one_of(st.none(), st.text(min_size=1, max_size=3)), min_size=1, max_size=3),
    types=st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=3)
)
def test_namedrowtuple_state(values, names, types):
    """Test __getstate__ and __setstate__ for proper state management."""
    min_len = min(len(values), len(names), len(types))
    values = values[:min_len]
    names = names[:min_len]
    types = types[:min_len]
    
    row = NamedRowTuple(values, names, types)
    state = row.__getstate__()
    
    # State should be the instance's __dict__
    assert state == vars(row)
    
    # Create a new row and set its state
    new_row = NamedRowTuple([0] * min_len, [""] * min_len, [""] * min_len)
    new_row.__setstate__(state)
    
    # Should have the same attributes
    assert new_row._names == row._names
    assert new_row._repr == row._repr