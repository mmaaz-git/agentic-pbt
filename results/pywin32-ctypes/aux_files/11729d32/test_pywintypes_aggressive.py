"""Aggressive property-based tests looking for bugs in win32ctypes.pywintypes."""

import sys
import time
import math
from datetime import datetime as std_datetime, timedelta

# Directly import just the pywintypes module without triggering other imports
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

# Import the specific module content to test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "pywintypes_test", 
    "/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages/win32ctypes/pywin32/pywintypes.py"
)
pywintypes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pywintypes)

from hypothesis import given, assume, strategies as st, settings, example

# Test boundary cases for timestamps
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
))
def test_time_with_special_floats(value):
    """Test Time with special float values."""
    try:
        result = pywintypes.Time(value)
        # Should probably raise an error for inf/nan
        print(f"Unexpected success with {value}: {result}")
    except (ValueError, OSError, OverflowError):
        # Expected
        pass


# Test with sequences containing invalid date values
@given(st.tuples(
    st.integers(),  # year - any integer
    st.integers(min_value=-100, max_value=100),  # month - including invalid
    st.integers(min_value=-100, max_value=100),  # day - including invalid
    st.integers(min_value=-100, max_value=100),  # hour
    st.integers(min_value=-100, max_value=100),  # minute
    st.integers(min_value=-100, max_value=100),  # second
    st.integers(min_value=-10, max_value=10),    # weekday
    st.integers(min_value=-1000, max_value=1000), # yearday
    st.integers(min_value=-2, max_value=2),      # isdst
))
@settings(max_examples=1000)
def test_time_with_invalid_date_components(time_tuple):
    """Test Time with potentially invalid date component values."""
    try:
        result = pywintypes.Time(time_tuple)
        # If it succeeds, verify it's a datetime
        assert isinstance(result, pywintypes.datetime)
        
        # Check if the values are actually valid
        rt = result.timetuple()
        # Basic sanity checks
        assert 1 <= rt.tm_mon <= 12
        assert 1 <= rt.tm_mday <= 31
        assert 0 <= rt.tm_hour <= 23
        assert 0 <= rt.tm_min <= 59
        assert 0 <= rt.tm_sec <= 60  # 60 for leap seconds
    except (ValueError, OverflowError, OSError):
        # Expected for invalid values
        pass


# Test sequences with None values
@given(st.lists(st.one_of(
    st.integers(min_value=0, max_value=2030),
    st.none(),
), min_size=9, max_size=10))
@settings(max_examples=500)
def test_time_with_none_in_sequence(seq):
    """Test Time with sequences containing None values."""
    try:
        result = pywintypes.Time(seq)
        assert isinstance(result, pywintypes.datetime)
    except (TypeError, ValueError, AttributeError, OSError):
        # Expected when None is in the sequence
        pass


# Test with objects that have weird timetuple implementations
class BadTimetuple1:
    def timetuple(self):
        raise RuntimeError("timetuple failed!")

class BadTimetuple2:
    def timetuple(self):
        return None

class BadTimetuple3:
    def timetuple(self):
        return "not a tuple"

class BadTimetuple4:
    def timetuple(self):
        return []  # Empty sequence

class BadTimetuple5:
    def timetuple(self):
        return (2020,)  # Too short

@given(st.sampled_from([
    BadTimetuple1(),
    BadTimetuple2(),
    BadTimetuple3(),
    BadTimetuple4(),
    BadTimetuple5(),
]))
@settings(max_examples=100)
def test_time_with_broken_timetuple_objects(obj):
    """Test Time with objects that have broken timetuple methods."""
    try:
        result = pywintypes.Time(obj)
        # Should probably fail
        print(f"Unexpected success with {obj.__class__.__name__}: {result}")
    except (RuntimeError, TypeError, ValueError, AttributeError, IndexError, OSError):
        # Expected
        pass


# Test Format with format strings containing null bytes
@given(
    st.floats(min_value=0, max_value=1893456000, allow_nan=False, allow_infinity=False),
    st.text().map(lambda s: s + '\x00' if s else '\x00')
)
@settings(max_examples=100)
def test_format_with_null_bytes(timestamp, fmt):
    """Test Format with format strings containing null bytes."""
    try:
        dt = pywintypes.Time(timestamp)
        result = dt.Format(fmt)
        expected = dt.strftime(fmt)
        assert result == expected
    except (ValueError, OSError):
        # Null bytes might cause issues
        pass


# Test very long format strings
@given(
    st.floats(min_value=0, max_value=1893456000, allow_nan=False, allow_infinity=False),
    st.text(min_size=1000, max_size=10000)
)
@settings(max_examples=10)
def test_format_with_very_long_strings(timestamp, fmt):
    """Test Format with very long format strings."""
    try:
        dt = pywintypes.Time(timestamp)
        result = dt.Format(fmt)
        expected = dt.strftime(fmt)
        assert result == expected
    except (ValueError, OSError, MemoryError):
        pass


# Test error class with many arguments
@given(st.lists(st.text(), min_size=100, max_size=1000))
@settings(max_examples=10)
def test_error_with_many_args(args):
    """Test error class with many arguments."""
    try:
        err = pywintypes.error(*args)
        # Should still only look at first 3
        assert err.winerror == args[0] if len(args) > 0 else None
        assert err.funcname == args[1] if len(args) > 1 else None
        assert err.strerror == args[2] if len(args) > 2 else None
    except Exception as e:
        print(f"Unexpected error with many args: {e}")


# Test Time with objects that change their timetuple between calls
class MutableTimetuple:
    def __init__(self):
        self.call_count = 0
    
    def timetuple(self):
        self.call_count += 1
        if self.call_count == 1:
            return (2020, 1, 1, 0, 0, 0, 0, 1, -1)
        else:
            return (2021, 12, 31, 23, 59, 59, 0, 365, -1)

@given(st.just(None))  # Dummy to make it a hypothesis test
@settings(max_examples=10)
def test_time_with_mutable_timetuple(dummy):
    """Test Time with objects whose timetuple changes."""
    obj = MutableTimetuple()
    result1 = pywintypes.Time(obj)
    # The timetuple was called once, should have 2020 date
    assert result1.year == 2020
    
    # Create another Time from the same object
    result2 = pywintypes.Time(obj)
    # Should now have 2021 date
    assert result2.year == 2021


# Test with sequences that have exactly 9 elements with extreme values
@given(st.tuples(
    st.integers(min_value=-1000000, max_value=1000000),  # year
    st.integers(min_value=-1000, max_value=1000),  # month
    st.integers(min_value=-1000, max_value=1000),  # day
    st.integers(min_value=-1000, max_value=1000),  # hour
    st.integers(min_value=-1000, max_value=1000),  # minute
    st.integers(min_value=-1000, max_value=1000),  # second
    st.integers(),  # weekday
    st.integers(),  # yearday
    st.integers(),  # isdst
))
@settings(max_examples=500)
def test_time_extreme_sequence_values(seq):
    """Test Time with sequences containing extreme values."""
    try:
        result = pywintypes.Time(seq)
        assert isinstance(result, pywintypes.datetime)
    except (ValueError, OverflowError, OSError):
        # Expected for extreme values
        pass


# Test precision loss with milliseconds
@given(st.integers(min_value=0, max_value=999))
@settings(max_examples=500)
def test_millisecond_precision_loss(millis):
    """Test if millisecond precision is preserved correctly."""
    time_tuple = (2020, 1, 1, 0, 0, 0, 0, 1, -1, millis)
    
    try:
        result = pywintypes.Time(time_tuple)
        
        # The implementation does: time_value += value[9] / 1000.0
        # This converts milliseconds to seconds (fractional part)
        # Then datetime.fromtimestamp should convert to microseconds
        
        # Expected microseconds
        expected_micros = millis * 1000
        
        # Check if there's precision loss
        actual_micros = result.microsecond
        
        # There might be some rounding due to float arithmetic
        diff = abs(actual_micros - expected_micros)
        
        # If difference is more than 1 microsecond, might be a precision issue
        if diff > 1:
            print(f"Precision loss: millis={millis}, expected_micros={expected_micros}, actual_micros={actual_micros}, diff={diff}")
            
        # Still assert within reasonable bounds
        assert diff <= 1000  # Should be within 1ms
        
    except (ValueError, OverflowError, OSError):
        pass


# Test that standard datetime and pywintypes.datetime behave differently with Time
@given(st.floats(min_value=0, max_value=1893456000, allow_nan=False, allow_infinity=False))
@settings(max_examples=500) 
def test_time_datetime_type_preservation(timestamp):
    """Test how Time handles different datetime types."""
    try:
        # Create a standard datetime
        std_dt = std_datetime.fromtimestamp(timestamp)
        
        # Pass it through Time
        result1 = pywintypes.Time(std_dt)
        
        # Result should be pywintypes.datetime, not standard datetime
        assert isinstance(result1, pywintypes.datetime)
        assert type(result1) is pywintypes.datetime
        
        # Now pass the pywintypes.datetime through Time again
        result2 = pywintypes.Time(result1)
        
        # Should return the same object (based on code: if isinstance(value, datetime): return value)
        assert result2 is result1
        
    except (ValueError, OSError):
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])  # -s to see print outputs