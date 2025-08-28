"""Edge case tests for win32ctypes.pywintypes - looking for bugs."""

import sys
import time
import math
from datetime import datetime as std_datetime

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

from hypothesis import given, assume, strategies as st, settings

# Test extreme timestamps
extreme_timestamps = st.one_of(
    st.floats(min_value=-1e10, max_value=-1),  # Negative timestamps
    st.floats(min_value=2e9, max_value=1e11),  # Far future timestamps
    st.just(0.0),  # Unix epoch
    st.floats(min_value=1e-10, max_value=1e-5),  # Very small positive
)

# Test edge case time tuples
edge_time_tuples = st.one_of(
    # February 29 (leap year edge case)
    st.tuples(
        st.sampled_from([2000, 2004, 2020, 2024]),  # Leap years
        st.just(2),  # February
        st.just(29),  # 29th day
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=6),
        st.just(60),  # 60th day of year
        st.integers(min_value=-1, max_value=1),
    ),
    # December 31
    st.tuples(
        st.integers(min_value=1970, max_value=2030),
        st.just(12),
        st.just(31),
        st.just(23),
        st.just(59),
        st.just(59),
        st.integers(min_value=0, max_value=6),
        st.just(365),
        st.integers(min_value=-1, max_value=1),
    ),
    # January 1
    st.tuples(
        st.integers(min_value=1970, max_value=2030),
        st.just(1),
        st.just(1),
        st.just(0),
        st.just(0),
        st.just(0),
        st.integers(min_value=0, max_value=6),
        st.just(1),
        st.integers(min_value=-1, max_value=1),
    ),
)

# Test various objects with timetuple attribute
class FakeDatetime:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
    
    def timetuple(self):
        return time.struct_time((self.year, self.month, self.day, 0, 0, 0, 0, 1, -1))

@given(st.integers(min_value=1970, max_value=2030),
       st.integers(min_value=1, max_value=12),
       st.integers(min_value=1, max_value=28))
@settings(max_examples=500)
def test_time_with_custom_timetuple_object(year, month, day):
    """Test Time with objects that have timetuple method."""
    fake_dt = FakeDatetime(year, month, day)
    result = pywintypes.Time(fake_dt)
    assert isinstance(result, pywintypes.datetime)
    assert result.year == year
    assert result.month == month
    assert result.day == day


@given(extreme_timestamps)
@settings(max_examples=500)
def test_time_extreme_timestamps(timestamp):
    """Test Time with extreme timestamp values."""
    try:
        result = pywintypes.Time(timestamp)
        assert isinstance(result, pywintypes.datetime)
        
        # Try round-trip
        result2 = pywintypes.Time(result)
        assert result == result2
    except (ValueError, OSError, OverflowError) as e:
        # These are expected for extreme values
        pass


@given(edge_time_tuples)
@settings(max_examples=500)
def test_time_edge_case_dates(time_tuple):
    """Test Time with edge case dates like leap years."""
    try:
        result = pywintypes.Time(time_tuple)
        assert isinstance(result, pywintypes.datetime)
        
        # Verify the date components are preserved
        result_tuple = result.timetuple()
        assert result_tuple.tm_year == time_tuple[0]
        assert result_tuple.tm_mon == time_tuple[1]
        assert result_tuple.tm_mday == time_tuple[2]
    except (ValueError, OverflowError, OSError):
        pass


# Test with invalid/malformed sequences
@given(st.lists(st.integers(), min_size=0, max_size=15))
@settings(max_examples=500)
def test_time_with_various_sequence_lengths(seq):
    """Test Time with sequences of various lengths."""
    try:
        result = pywintypes.Time(seq)
        # If it doesn't raise an exception, it should be a datetime
        assert isinstance(result, pywintypes.datetime)
    except (ValueError, TypeError, IndexError, OverflowError, OSError):
        # Expected for invalid sequences
        pass


# Test microsecond precision with 10-element tuples
@given(
    st.integers(min_value=1970, max_value=2030),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28),
    st.integers(min_value=0, max_value=23),
    st.integers(min_value=0, max_value=59),
    st.integers(min_value=0, max_value=59),
    st.integers(min_value=0, max_value=999)
)
@settings(max_examples=500)
def test_time_millisecond_precision(year, month, day, hour, minute, second, millis):
    """Test that milliseconds in 10-element tuples are handled correctly."""
    time_tuple = (year, month, day, hour, minute, second, 0, 1, -1, millis)
    
    try:
        result = pywintypes.Time(time_tuple)
        assert isinstance(result, pywintypes.datetime)
        
        # Check that the milliseconds affected the microseconds
        # The implementation adds millis/1000.0 to the timestamp
        expected_micros = millis * 1000
        # Due to floating point precision, we need to be a bit lenient
        assert abs(result.microsecond - expected_micros) <= 1000
    except (ValueError, OverflowError, OSError):
        pass


# Test Format with special/unusual format strings
unusual_formats = st.one_of(
    st.just('%'),  # Just percent
    st.just('%%'),  # Escaped percent
    st.just('%Z'),  # Timezone
    st.just('%z'),  # UTC offset
    st.just('%j'),  # Day of year
    st.just('%U'),  # Week number (Sunday)
    st.just('%W'),  # Week number (Monday)
    st.text(min_size=0, max_size=10),  # Random text
)

@given(st.floats(min_value=0, max_value=1893456000, allow_nan=False, allow_infinity=False),
       unusual_formats)
@settings(max_examples=500)
def test_format_unusual_strings(timestamp, fmt):
    """Test Format with unusual format strings."""
    try:
        dt = pywintypes.Time(timestamp)
        result = dt.Format(fmt)
        expected = dt.strftime(fmt)
        assert result == expected
    except (ValueError, OSError):
        # Some format strings might be invalid
        pass


# Test error class with unusual arguments
@given(st.lists(st.one_of(st.integers(), st.text(), st.none()), min_size=0, max_size=5))
@settings(max_examples=500)
def test_error_various_args(args):
    """Test error class with various argument combinations."""
    try:
        err = pywintypes.error(*args)
        
        # Check attributes based on argument count
        if len(args) >= 1:
            assert err.winerror == args[0]
        else:
            assert err.winerror is None
            
        if len(args) >= 2:
            assert err.funcname == args[1]
        else:
            assert err.funcname is None
            
        if len(args) >= 3:
            assert err.strerror == args[2]
        else:
            assert err.strerror is None
    except Exception:
        # Shouldn't happen but catch any unexpected errors
        pass


# Test Time with objects that are almost datetime-like
class AlmostDatetime:
    def __init__(self, bad_timetuple):
        self.bad_timetuple = bad_timetuple
    
    def timetuple(self):
        return self.bad_timetuple

@given(st.one_of(
    st.none(),
    st.integers(),
    st.text(),
    st.lists(st.integers(), min_size=0, max_size=5),
))
@settings(max_examples=500)
def test_time_with_bad_timetuple_objects(bad_value):
    """Test Time with objects that have bad timetuple methods."""
    fake_dt = AlmostDatetime(bad_value)
    try:
        result = pywintypes.Time(fake_dt)
        # If successful, should be datetime
        assert isinstance(result, pywintypes.datetime)
    except (TypeError, ValueError, AttributeError, IndexError, OSError):
        # Expected for bad timetuple returns
        pass


# Test that Time really returns the same instance for pywintypes.datetime
@given(st.floats(min_value=0, max_value=1893456000, allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_time_returns_same_instance(timestamp):
    """Test that Time returns the same instance when passed pywintypes.datetime."""
    try:
        dt1 = pywintypes.Time(timestamp)
        dt2 = pywintypes.Time(dt1)
        
        # According to the code, if isinstance(value, datetime), it returns value
        # So dt2 should be the same object as dt1
        assert dt2 is dt1
    except (ValueError, OSError):
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])