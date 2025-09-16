"""
Test metamorphic properties and parsing consistency in dateutil.parser.
Look for violations of expected relationships between inputs and outputs.
"""
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings, seed
import dateutil.parser
import pytest


@given(st.text(min_size=1, max_size=30))
def test_adding_spaces_preserves_parse(text):
    """Test that adding leading/trailing spaces doesn't change parse result."""
    try:
        original = dateutil.parser.parse(text)
        with_spaces = dateutil.parser.parse(f"  {text}  ")
        assert original == with_spaces
    except dateutil.parser.ParserError:
        # Both should fail
        with pytest.raises(dateutil.parser.ParserError):
            dateutil.parser.parse(f"  {text}  ")


@given(st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)))
def test_date_and_datetime_parsing_consistency(dt):
    """Test that date-only string parses consistently."""
    date_str = dt.date().isoformat()
    
    # Parse as date string
    parsed1 = dateutil.parser.parse(date_str)
    
    # Parse with explicit time 00:00:00
    datetime_str = f"{date_str}T00:00:00"
    parsed2 = dateutil.parser.parse(datetime_str)
    
    # Should be the same
    assert parsed1 == parsed2


@given(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
def test_24hour_vs_12hour_consistency(hour, minute, second):
    """Test 24-hour vs 12-hour format consistency."""
    # 24-hour format
    time_24h = f"{hour:02d}:{minute:02d}:{second:02d}"
    
    # Convert to 12-hour format
    if hour == 0:
        hour_12 = 12
        meridiem = "AM"
    elif hour < 12:
        hour_12 = hour
        meridiem = "AM"
    elif hour == 12:
        hour_12 = 12
        meridiem = "PM"
    else:
        hour_12 = hour - 12
        meridiem = "PM"
    
    time_12h = f"{hour_12}:{minute:02d}:{second:02d} {meridiem}"
    
    # Parse both with a default date
    default = datetime(2024, 1, 1)
    parsed_24h = dateutil.parser.parse(time_24h, default=default)
    parsed_12h = dateutil.parser.parse(time_12h, default=default)
    
    # Should give the same time
    assert parsed_24h == parsed_12h


@given(st.integers(1, 9999))
def test_year_parsing_consistency(year):
    """Test that different year formats parse consistently."""
    # Full year format
    full_year = f"{year:04d}-01-01"
    parsed_full = dateutil.parser.parse(full_year)
    
    # Year with different date formats
    formats = [
        f"{year}/01/01",
        f"{year}.01.01",
        f"01-01-{year}",
        f"01/01/{year}",
        f"January 1, {year}",
        f"1 Jan {year}",
    ]
    
    for fmt in formats:
        try:
            parsed = dateutil.parser.parse(fmt)
            assert parsed.year == year
            assert parsed.month == 1
            assert parsed.day == 1
        except dateutil.parser.ParserError:
            pass


@given(st.integers(1, 12), st.integers(1, 28))  # Use 28 to avoid month-end issues
def test_month_day_order_with_explicit_params(month, day):
    """Test dayfirst and monthfirst parameters."""
    ambiguous_str = f"{month:02d}-{day:02d}-2024"
    
    # Parse with different settings
    parsed_default = dateutil.parser.parse(ambiguous_str)
    parsed_dayfirst = dateutil.parser.parse(ambiguous_str, dayfirst=True)
    parsed_monthfirst = dateutil.parser.parse(ambiguous_str, dayfirst=False)
    
    if month != day and month <= 12 and day <= 12:
        # When ambiguous, dayfirst should affect the result
        if month <= 12 and day <= 12:
            assert parsed_dayfirst.month == day or parsed_dayfirst.day == day
            assert parsed_monthfirst.month == month or parsed_monthfirst.day == month


@given(st.datetimes())
def test_parsing_stringified_datetime_preserves_value(dt):
    """Test that str(datetime) -> parse gives back the same datetime."""
    dt_str = str(dt)
    parsed = dateutil.parser.parse(dt_str)
    assert parsed == dt


@given(st.integers(0, 999999))
def test_microsecond_string_formats(microseconds):
    """Test different microsecond string representations."""
    dt = datetime(2024, 1, 1, 0, 0, 0, microseconds)
    
    # Different ways to represent the same datetime
    formats = [
        dt.isoformat(),
        str(dt),
        dt.strftime("%Y-%m-%d %H:%M:%S.%f") if microseconds > 0 else dt.strftime("%Y-%m-%d %H:%M:%S"),
    ]
    
    parsed_values = []
    for fmt in formats:
        try:
            parsed = dateutil.parser.parse(fmt)
            parsed_values.append(parsed)
        except dateutil.parser.ParserError:
            pass
    
    # All successful parses should give the same result
    if parsed_values:
        assert all(p == parsed_values[0] for p in parsed_values)


@given(st.sampled_from(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))
def test_weekday_ignored_property(weekday):
    """Test that weekday names don't affect the parsed date when date is explicit."""
    # Create dates with incorrect weekdays
    test_cases = [
        f"{weekday}, 2024-01-15",  # Monday, but date might be different day
        f"{weekday} 2024-01-15",
        f"2024-01-15 {weekday}",
    ]
    
    for test_str in test_cases:
        try:
            parsed = dateutil.parser.parse(test_str)
            # Should always parse to Jan 15, 2024 regardless of weekday name
            assert parsed.year == 2024
            assert parsed.month == 1
            assert parsed.day == 15
        except dateutil.parser.ParserError:
            pass


@given(st.integers(-23, 23), st.integers(0, 59))
def test_timezone_offset_sign_handling(hours, minutes):
    """Test that timezone offset signs are handled correctly."""
    # Create offset strings
    if hours >= 0:
        offset_str1 = f"+{hours:02d}:{minutes:02d}"
        offset_str2 = f"+{hours:02d}{minutes:02d}"
    else:
        offset_str1 = f"-{abs(hours):02d}:{minutes:02d}"
        offset_str2 = f"-{abs(hours):02d}{minutes:02d}"
    
    dt_str1 = f"2024-01-01T12:00:00{offset_str1}"
    dt_str2 = f"2024-01-01T12:00:00{offset_str2}"
    
    try:
        parsed1 = dateutil.parser.isoparse(dt_str1)
        parsed2 = dateutil.parser.isoparse(dt_str2)
        
        # Both formats should give the same result
        if parsed1.tzinfo and parsed2.tzinfo:
            offset1 = parsed1.tzinfo.utcoffset(parsed1)
            offset2 = parsed2.tzinfo.utcoffset(parsed2)
            assert offset1 == offset2
    except (ValueError, dateutil.parser.ParserError):
        pass


@given(st.floats(min_value=0.0, max_value=0.999999))
def test_fractional_seconds_truncation(fraction):
    """Test that fractional seconds are truncated, not rounded."""
    # Create a time with specific fractional seconds
    microseconds = int(fraction * 1000000)
    
    # Create string with more precision than microseconds can handle
    frac_str = f"{fraction:.9f}".rstrip('0')
    if '.' in frac_str:
        dt_str = f"2024-01-01T00:00:00{frac_str[1:]}"  # Skip the leading 0
    else:
        dt_str = "2024-01-01T00:00:00"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        # Should truncate, not round
        assert parsed.microsecond == microseconds
    except (ValueError, dateutil.parser.ParserError):
        pass


@given(st.sampled_from(['Z', '+00:00', '-00:00', '+0000', '-0000']))
def test_utc_representations_equivalent(utc_str):
    """Test that different UTC representations are equivalent."""
    dt_str = f"2024-01-01T12:00:00{utc_str}"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        if parsed.tzinfo:
            offset = parsed.tzinfo.utcoffset(parsed)
            # All should represent UTC (zero offset)
            assert offset == timedelta(0) or offset is None
    except (ValueError, dateutil.parser.ParserError, AttributeError):
        pass


@given(st.text(min_size=1, max_size=20))
def test_fuzzy_parse_subset_property(text):
    """Test that fuzzy parsing extracts a subset of the input."""
    # Add a known date to ensure there's something to parse
    full_text = f"noise {text} 2024-01-15 {text} noise"
    
    try:
        parsed = dateutil.parser.parse(full_text, fuzzy=True)
        # The parsed date should be the one we added
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.integers(1, 9999), st.integers(1, 12), st.integers(1, 28))
def test_default_parameter_partial_override(year, month, day):
    """Test that default parameter correctly fills missing components."""
    default_dt = datetime(year, month, day, 10, 20, 30, 123456)
    
    # Test with only time specified
    time_only = "15:45:50"
    parsed = dateutil.parser.parse(time_only, default=default_dt)
    
    # Date from default, time from string
    assert parsed.year == year
    assert parsed.month == month
    assert parsed.day == day
    assert parsed.hour == 15
    assert parsed.minute == 45
    assert parsed.second == 50
    
    # Test with only date specified
    date_only = "2020-06-15"
    parsed = dateutil.parser.parse(date_only, default=default_dt)
    
    # Date from string, time from default
    assert parsed.year == 2020
    assert parsed.month == 6
    assert parsed.day == 15
    assert parsed.hour == default_dt.hour
    assert parsed.minute == default_dt.minute
    assert parsed.second == default_dt.second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])