#!/usr/bin/env python3
"""Property-based tests for rarfile module using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/rarfile_env/lib/python3.13/site-packages')

import rarfile
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
import pytest


# Test 1: parse_dos_time should produce valid date/time tuples
@given(st.integers(min_value=0, max_value=0xFFFFFFFF))
def test_parse_dos_time_valid_output(stamp):
    """parse_dos_time should always return a valid date/time tuple."""
    result = rarfile.parse_dos_time(stamp)
    
    # Check it returns a 6-tuple
    assert isinstance(result, tuple)
    assert len(result) == 6
    
    year, month, day, hour, minute, second = result
    
    # Check ranges based on DOS timestamp format
    # Year: 7 bits (0-127) + 1980 = 1980-2107
    assert 1980 <= year <= 2107
    # Month: 4 bits (0-15) 
    assert 0 <= month <= 15
    # Day: 5 bits (0-31)
    assert 0 <= day <= 31
    # Hour: 5 bits (0-31)
    assert 0 <= hour <= 31
    # Minute: 6 bits (0-63)
    assert 0 <= minute <= 63
    # Second: 5 bits * 2 (0-62, even numbers only)
    assert 0 <= second <= 62
    assert second % 2 == 0


# Test 2: sanitize_filename idempotence
@given(st.text(min_size=0, max_size=255))
@settings(max_examples=1000)
def test_sanitize_filename_idempotence(filename):
    """sanitize_filename should be idempotent: f(f(x)) = f(x)"""
    # Test on both Windows and Unix
    for is_win32 in [True, False]:
        pathsep = "\\" if is_win32 else "/"
        
        # Apply once
        sanitized_once = rarfile.sanitize_filename(filename, pathsep, is_win32)
        
        # Apply twice  
        sanitized_twice = rarfile.sanitize_filename(sanitized_once, pathsep, is_win32)
        
        # Should be the same
        assert sanitized_once == sanitized_twice


# Test 3: to_datetime should handle any 6-tuple without raising exceptions
@given(
    st.tuples(
        st.integers(min_value=1, max_value=9999),  # year
        st.integers(min_value=-100, max_value=100),  # month (including invalid)
        st.integers(min_value=-100, max_value=100),  # day (including invalid)
        st.integers(min_value=-100, max_value=100),  # hour (including invalid)
        st.integers(min_value=-100, max_value=100),  # minute (including invalid)
        st.integers(min_value=-100, max_value=100),  # second (including invalid)
    )
)
def test_to_datetime_sanitization(time_tuple):
    """to_datetime claims to sanitize invalid values - should never raise exception."""
    result = rarfile.to_datetime(time_tuple)
    
    # Should always return a datetime object
    assert isinstance(result, datetime)
    
    # The result should be a valid datetime (Python datetime constructor would have validated it)
    assert 1 <= result.month <= 12
    assert 1 <= result.day <= 31
    assert 0 <= result.hour <= 23
    assert 0 <= result.minute <= 59
    assert 0 <= result.second <= 59


# Test 4: nsdatetime nanosecond preservation
@given(
    st.integers(min_value=1, max_value=9999),  # year
    st.integers(min_value=1, max_value=12),    # month
    st.integers(min_value=1, max_value=28),    # day (safe for all months)
    st.integers(min_value=0, max_value=23),    # hour
    st.integers(min_value=0, max_value=59),    # minute
    st.integers(min_value=0, max_value=59),    # second
    st.integers(min_value=0, max_value=999999999)  # nanosecond
)
def test_nsdatetime_nanosecond_preservation(year, month, day, hour, minute, second, nanosecond):
    """nsdatetime should preserve nanosecond field as documented."""
    dt = rarfile.nsdatetime(year, month, day, hour, minute, second, nanosecond=nanosecond)
    
    # Check nanosecond is preserved
    if nanosecond % 1000 != 0:  # Only if nanosecond precision is actually needed
        assert hasattr(dt, 'nanosecond')
        assert dt.nanosecond == nanosecond
    
    # Test that replace preserves nanoseconds when not explicitly changed
    if hasattr(dt, 'nanosecond'):
        dt2 = dt.replace(hour=12)
        assert dt2.nanosecond == nanosecond


# Test 5: load_vint should successfully parse valid vint buffers
@given(st.integers(min_value=0, max_value=0x7FFFFFFF))  # Reasonable vint range
def test_load_vint_roundtrip(value):
    """load_vint should be able to parse valid vint-encoded integers."""
    # Encode the value as a vint
    buf = bytearray()
    temp = value
    while temp >= 0x80:
        buf.append(0x80 | (temp & 0x7F))
        temp >>= 7
    buf.append(temp)
    
    # Try to load it back
    loaded_value, pos = rarfile.load_vint(bytes(buf), 0)
    
    # Should get the same value back
    assert loaded_value == value
    assert pos == len(buf)


# Test 6: parse_dos_time -> to_datetime composition
@given(st.integers(min_value=0, max_value=0xFFFFFFFF))
def test_parse_dos_time_to_datetime_composition(stamp):
    """parse_dos_time followed by to_datetime should always produce valid datetime."""
    time_tuple = rarfile.parse_dos_time(stamp)
    dt = rarfile.to_datetime(time_tuple)
    
    # Should always succeed and produce valid datetime
    assert isinstance(dt, datetime)
    
    # Verify the datetime is reasonable for DOS timestamps
    assert 1980 <= dt.year <= 2107  # DOS timestamp year range


# Test 7: Path manipulation in sanitize_filename
@given(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10))
def test_sanitize_filename_path_segments(segments):
    """sanitize_filename should handle path segments correctly."""
    # Create a path with forward slashes
    filename = "/".join(segments)
    
    for is_win32 in [True, False]:
        pathsep = "\\" if is_win32 else "/"
        result = rarfile.sanitize_filename(filename, pathsep, is_win32)
        
        # Empty segments, ".", and ".." should be removed
        if result:
            result_segments = result.split(pathsep)
            for seg in result_segments:
                assert seg not in ("", ".", "..")
                assert len(seg) > 0


if __name__ == "__main__":
    # Run with pytest for better output
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])