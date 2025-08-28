"""Property-based tests for win32ctypes.pywintypes using Hypothesis."""

import sys
import time
import math
from datetime import datetime as std_datetime

sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
from win32ctypes.pywin32 import pywintypes


# Strategy for reasonable timestamps (avoiding overflow issues)
# Using range from year 1970 to 2030
safe_timestamps = st.floats(
    min_value=0,  # Unix epoch
    max_value=1893456000,  # Year 2030
    allow_nan=False,
    allow_infinity=False
)

# Strategy for time tuples with valid ranges
time_tuples = st.tuples(
    st.integers(min_value=1970, max_value=2030),  # year
    st.integers(min_value=1, max_value=12),  # month
    st.integers(min_value=1, max_value=28),  # day (simplified to avoid month edge cases)
    st.integers(min_value=0, max_value=23),  # hour
    st.integers(min_value=0, max_value=59),  # minute
    st.integers(min_value=0, max_value=59),  # second
    st.integers(min_value=0, max_value=6),   # weekday
    st.integers(min_value=1, max_value=365), # yearday (simplified)
    st.integers(min_value=-1, max_value=1),  # isdst
)

# Strategy for valid datetime format strings
format_strings = st.sampled_from([
    '%Y-%m-%d',
    '%Y-%m-%d %H:%M:%S',
    '%c',
    '%x',
    '%X',
    '%Y',
    '%m/%d/%Y',
    '%H:%M',
    '%B %d, %Y',
    '%A',
])


@given(safe_timestamps)
@settings(max_examples=1000)
def test_time_timestamp_round_trip(timestamp):
    """Test that Time function properly handles timestamps and round-trips."""
    try:
        dt1 = pywintypes.Time(timestamp)
        dt2 = pywintypes.Time(dt1)
        # Should be idempotent
        assert dt1 == dt2
        assert isinstance(dt1, pywintypes.datetime)
    except (ValueError, OSError):
        # Some timestamps might be invalid on the system
        pass


@given(time_tuples)
@settings(max_examples=1000)
def test_time_with_sequences(time_tuple):
    """Test that Time function converts time tuples to datetime objects."""
    try:
        result = pywintypes.Time(time_tuple)
        assert isinstance(result, pywintypes.datetime)
        
        # Convert back to time tuple and check some fields match
        result_tuple = result.timetuple()
        assert result_tuple.tm_year == time_tuple[0]
        assert result_tuple.tm_mon == time_tuple[1]
        assert result_tuple.tm_mday == time_tuple[2]
        assert result_tuple.tm_hour == time_tuple[3]
        assert result_tuple.tm_min == time_tuple[4]
        assert result_tuple.tm_sec == time_tuple[5]
    except (ValueError, OverflowError, OSError):
        # Some combinations might be invalid dates
        pass


@given(time_tuples, st.integers(min_value=0, max_value=999))
@settings(max_examples=500)
def test_time_with_10_element_sequences(time_tuple, milliseconds):
    """Test Time function with 10-element sequences (including milliseconds)."""
    extended_tuple = time_tuple + (milliseconds,)
    try:
        result = pywintypes.Time(extended_tuple)
        assert isinstance(result, pywintypes.datetime)
        
        # The milliseconds should affect the microseconds
        # Note: milliseconds are divided by 1000.0 in the implementation
        result_tuple = result.timetuple()
        assert result_tuple.tm_year == time_tuple[0]
        assert result_tuple.tm_mon == time_tuple[1]
        assert result_tuple.tm_mday == time_tuple[2]
    except (ValueError, OverflowError, OSError):
        pass


@given(safe_timestamps, format_strings)
@settings(max_examples=500)
def test_datetime_format_equivalence(timestamp, fmt):
    """Test that datetime.Format matches strftime behavior."""
    try:
        dt = pywintypes.Time(timestamp)
        
        # Test Format method
        formatted = dt.Format(fmt)
        strftime_result = dt.strftime(fmt)
        
        assert formatted == strftime_result
    except (ValueError, OSError):
        pass


@given(safe_timestamps)
@settings(max_examples=500)
def test_datetime_format_default(timestamp):
    """Test that datetime.Format with no args uses '%c' as default."""
    try:
        dt = pywintypes.Time(timestamp)
        
        # Default should be '%c'
        default_format = dt.Format()
        explicit_format = dt.Format('%c')
        strftime_c = dt.strftime('%c')
        
        assert default_format == explicit_format
        assert default_format == strftime_c
    except (ValueError, OSError):
        pass


@given(
    st.one_of(st.none(), st.integers()),
    st.one_of(st.none(), st.text()),
    st.one_of(st.none(), st.text())
)
@settings(max_examples=500)
def test_error_class_initialization(winerror, funcname, strerror):
    """Test that error class properly initializes attributes."""
    # Test with different argument combinations
    if winerror is not None and funcname is not None and strerror is not None:
        err = pywintypes.error(winerror, funcname, strerror)
        assert err.winerror == winerror
        assert err.funcname == funcname
        assert err.strerror == strerror
    elif winerror is not None and funcname is not None:
        err = pywintypes.error(winerror, funcname)
        assert err.winerror == winerror
        assert err.funcname == funcname
        assert err.strerror is None
    elif winerror is not None:
        err = pywintypes.error(winerror)
        assert err.winerror == winerror
        assert err.funcname is None
        assert err.strerror is None
    else:
        err = pywintypes.error()
        assert err.winerror is None
        assert err.funcname is None
        assert err.strerror is None


@given(st.data())
@settings(max_examples=500)
def test_time_datetime_invariant(data):
    """Test that Time preserves datetime objects that are already pywintypes.datetime."""
    timestamp = data.draw(safe_timestamps)
    try:
        dt = pywintypes.Time(timestamp)
        # When passing a datetime to Time, it should return the same object
        result = pywintypes.Time(dt)
        assert result is dt or result == dt
        assert isinstance(result, pywintypes.datetime)
    except (ValueError, OSError):
        pass


@given(safe_timestamps)
@settings(max_examples=500)
def test_time_handles_standard_datetime(timestamp):
    """Test that Time can handle standard Python datetime objects."""
    try:
        std_dt = std_datetime.fromtimestamp(timestamp)
        result = pywintypes.Time(std_dt)
        assert isinstance(result, pywintypes.datetime)
        
        # Should preserve the time information
        assert result.year == std_dt.year
        assert result.month == std_dt.month
        assert result.day == std_dt.day
        assert result.hour == std_dt.hour
        assert result.minute == std_dt.minute
        assert result.second == std_dt.second
    except (ValueError, OSError):
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])