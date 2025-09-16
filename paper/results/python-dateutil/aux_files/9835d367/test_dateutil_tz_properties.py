#!/usr/bin/env python3
"""Property-based tests for dateutil.tz module"""

from hypothesis import given, strategies as st, assume, settings
import dateutil.tz
from datetime import datetime, timedelta
import pytest

# Strategy for generating valid timezone objects
@st.composite
def timezone_strategy(draw):
    tz_choices = [
        dateutil.tz.tzutc(),
        dateutil.tz.tzlocal(),
        dateutil.tz.gettz('America/New_York'),
        dateutil.tz.gettz('Europe/London'),
        dateutil.tz.gettz('Pacific/Kiritimati'),
        dateutil.tz.gettz('America/Sao_Paulo'),
        dateutil.tz.gettz('Australia/Lord_Howe'),  # has 30-minute DST offset
    ]
    # Filter out None values (in case gettz fails)
    valid_tzs = [tz for tz in tz_choices if tz is not None]
    return draw(st.sampled_from(valid_tzs))

# Strategy for generating datetimes that might be near DST transitions
@st.composite
def datetime_strategy(draw):
    year = draw(st.integers(min_value=1900, max_value=2100))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # avoid month-end issues
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return datetime(year, month, day, hour, minute, second)

# Property 1: A datetime cannot be both non-existent and ambiguous
@given(dt=datetime_strategy(), tz=timezone_strategy())
def test_datetime_exists_ambiguous_exclusive(dt, tz):
    """A datetime cannot be both non-existent and ambiguous"""
    exists = dateutil.tz.datetime_exists(dt, tz)
    ambiguous = dateutil.tz.datetime_ambiguous(dt, tz)
    
    # If it doesn't exist, it can't be ambiguous
    if not exists:
        assert not ambiguous, f"DateTime {dt} in {tz} is both non-existent and ambiguous"

# Property 2: resolve_imaginary is idempotent
@given(dt=datetime_strategy(), tz=timezone_strategy())
def test_resolve_imaginary_idempotent(dt, tz):
    """Resolving an imaginary datetime twice should give the same result"""
    dt_with_tz = dt.replace(tzinfo=tz)
    resolved_once = dateutil.tz.resolve_imaginary(dt_with_tz)
    resolved_twice = dateutil.tz.resolve_imaginary(resolved_once)
    
    assert resolved_once == resolved_twice, f"resolve_imaginary is not idempotent for {dt_with_tz}"

# Property 3: enfold with fold=0 and fold=1 should only differ for ambiguous times
@given(dt=datetime_strategy(), tz=timezone_strategy())
def test_enfold_fold_difference(dt, tz):
    """enfold with different fold values should only differ for ambiguous times"""
    dt_with_tz = dt.replace(tzinfo=tz)
    
    folded_0 = dateutil.tz.enfold(dt_with_tz, fold=0)
    folded_1 = dateutil.tz.enfold(dt_with_tz, fold=1)
    
    is_ambiguous = dateutil.tz.datetime_ambiguous(dt, tz)
    
    # Get UTC offsets for both fold values
    offset_0 = folded_0.utcoffset() if folded_0.tzinfo else None
    offset_1 = folded_1.utcoffset() if folded_1.tzinfo else None
    
    if not is_ambiguous:
        # For non-ambiguous times, fold should not affect the UTC offset
        assert offset_0 == offset_1, f"Non-ambiguous datetime {dt} has different offsets with different fold values"

# Property 4: Valid datetimes should round-trip through UTC
@given(dt=datetime_strategy(), tz=timezone_strategy())
def test_utc_roundtrip_for_existing_datetimes(dt, tz):
    """Valid (existing) datetimes should round-trip through UTC"""
    if dateutil.tz.datetime_exists(dt, tz):
        dt_with_tz = dt.replace(tzinfo=tz)
        
        # Round trip through UTC
        utc_dt = dt_with_tz.astimezone(dateutil.tz.tzutc())
        back_dt = utc_dt.astimezone(tz)
        
        # The datetime should be the same after round-trip
        assert back_dt.replace(tzinfo=None) == dt, f"DateTime {dt} didn't round-trip correctly through UTC"

# Property 5: datetime_exists implementation consistency check
@given(dt=datetime_strategy(), tz=timezone_strategy())
def test_datetime_exists_implementation(dt, tz):
    """Test datetime_exists by checking its implementation logic"""
    exists = dateutil.tz.datetime_exists(dt, tz)
    
    # Manually check using the same logic as datetime_exists
    dt_test = dt.replace(tzinfo=tz)
    try:
        dt_rt = dt_test.astimezone(dateutil.tz.tzutc()).astimezone(tz)
        dt_rt_naive = dt_rt.replace(tzinfo=None)
        manual_exists = (dt == dt_rt_naive)
    except:
        # If conversion fails, datetime doesn't exist
        manual_exists = False
    
    assert exists == manual_exists, f"datetime_exists result doesn't match manual check for {dt} in {tz}"

# Property 6: tzical offset parsing round-trip
@given(hours=st.integers(min_value=-23, max_value=23),
       minutes=st.integers(min_value=0, max_value=59))
def test_tzical_offset_parse_format(hours, minutes):
    """Test that offset parsing and formatting are consistent"""
    tzical = dateutil.tz.tzical()
    
    # Create offset string
    total_seconds = hours * 3600 + minutes * 60
    sign = '+' if total_seconds >= 0 else '-'
    abs_hours = abs(hours)
    abs_minutes = abs(minutes)
    
    # Test 4-character format (HHMM)
    offset_str_4 = f"{sign}{abs_hours:02d}{abs_minutes:02d}"
    try:
        parsed_offset = tzical._parse_offset(offset_str_4)
        expected_offset = total_seconds
        
        # Account for sign handling
        if sign == '-':
            expected_offset = -(abs_hours * 3600 + abs_minutes * 60)
        else:
            expected_offset = abs_hours * 3600 + abs_minutes * 60
            
        assert parsed_offset == expected_offset, f"Offset parsing failed for {offset_str_4}"
    except ValueError:
        # Some offsets might be invalid
        pass

# Property 7: Empty value handling in tzical._parse_offset
@given(st.just(""))
def test_tzical_parse_offset_empty(empty_str):
    """Test that empty offset string raises ValueError"""
    tzical = dateutil.tz.tzical()
    
    with pytest.raises(ValueError, match="empty offset"):
        tzical._parse_offset(empty_str)

# Property 8: tzical._parse_offset with whitespace-only strings
@given(st.text(alphabet=' \t\n\r', min_size=1, max_size=10))
def test_tzical_parse_offset_whitespace(whitespace_str):
    """Test that whitespace-only strings raise ValueError after stripping"""
    tzical = dateutil.tz.tzical()
    
    # After stripping, these should become empty and raise "empty offset" error
    with pytest.raises(ValueError, match="empty offset"):
        tzical._parse_offset(whitespace_str)

if __name__ == "__main__":
    # Run the tests with increased examples for better coverage
    import sys
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])