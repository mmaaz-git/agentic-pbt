"""
More aggressive property-based tests for dateutil.parser to find bugs.
"""
import math
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, assume, settings, example
import dateutil.parser
import dateutil.tz
import pytest


# Test for unusual ISO format variations
@given(st.integers(1, 9999), st.integers(1, 366))
def test_ordinal_date_format(year, day_of_year):
    """Test parsing ordinal date format (YYYY-DDD)."""
    # Adjust for leap years
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    max_days = 366 if is_leap else 365
    assume(day_of_year <= max_days)
    
    ordinal_str = f"{year:04d}-{day_of_year:03d}"
    try:
        parsed = dateutil.parser.isoparse(ordinal_str)
        # Calculate expected date
        from datetime import date, timedelta
        expected = date(year, 1, 1) + timedelta(days=day_of_year - 1)
        assert parsed.date() == expected
    except (ValueError, dateutil.parser.ParserError):
        # isoparse might not support ordinal dates
        pass


@given(st.integers(1, 9999), st.integers(1, 53), st.integers(1, 7))
def test_week_date_format(year, week, day):
    """Test parsing week date format (YYYY-Www-D)."""
    week_str = f"{year:04d}-W{week:02d}-{day}"
    try:
        parsed = dateutil.parser.isoparse(week_str)
        assert isinstance(parsed, datetime)
    except (ValueError, dateutil.parser.ParserError, AttributeError):
        # isoparse might not support week dates
        pass


@given(st.text(alphabet="0123456789-+:TZ .", min_size=1, max_size=50))
def test_malformed_datetime_strings(s):
    """Test parsing of strings that look like datetimes but might be malformed."""
    try:
        result = dateutil.parser.parse(s)
        # If it parses, verify it's a valid datetime
        assert isinstance(result, datetime)
        assert 1 <= result.year <= 9999
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_timestamp_parsing(timestamp):
    """Test parsing Unix timestamps."""
    timestamp_str = str(int(timestamp))
    try:
        result = dateutil.parser.parse(timestamp_str)
        assert isinstance(result, datetime)
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.integers(0, 99))
def test_two_digit_year_parsing(year):
    """Test parsing two-digit years."""
    year_str = f"{year:02d}-01-01"
    try:
        parsed = dateutil.parser.parse(year_str)
        # Two-digit years should be interpreted with a pivot
        assert isinstance(parsed, datetime)
        # Check century wrapping logic
        if year >= 69:
            assert parsed.year == 1900 + year
        else:
            assert parsed.year == 2000 + year
    except (dateutil.parser.ParserError, ValueError):
        pass


@given(st.lists(st.integers(1, 12), min_size=1, max_size=5))
def test_multiple_date_components_in_string(months):
    """Test strings with multiple potential date components."""
    date_str = "-".join([f"{m:02d}" for m in months])
    try:
        result = dateutil.parser.parse(date_str)
        assert isinstance(result, datetime)
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.text(alphabet="0123456789", min_size=14, max_size=14))
def test_yyyymmddhhmmss_format(s):
    """Test parsing compact datetime format."""
    try:
        result = dateutil.parser.parse(s)
        assert isinstance(result, datetime)
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.integers(-10000, 10000), st.integers(-100, 100))
def test_extreme_years_and_offsets(year, offset_hours):
    """Test parsing extreme years with timezone offsets."""
    if year < 1 or year > 9999:
        return  # Skip invalid years for datetime
    
    # Clamp offset to valid range
    offset_hours = max(-24, min(24, offset_hours))
    sign = '+' if offset_hours >= 0 else '-'
    
    dt_str = f"{year:04d}-01-01T00:00:00{sign}{abs(offset_hours):02d}:00"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        assert parsed.year == year
    except (ValueError, dateutil.parser.ParserError, OverflowError):
        pass


@given(st.floats(min_value=0, max_value=999999999, allow_nan=False, allow_infinity=False))
def test_fractional_seconds_edge_cases(fraction):
    """Test edge cases in fractional seconds parsing."""
    # Create string with many decimal places
    frac_str = f"{fraction:.9f}".rstrip('0').rstrip('.')
    if '.' in frac_str:
        decimal_part = frac_str.split('.')[1]
        dt_str = f"2024-01-01T00:00:00.{decimal_part}"
    else:
        dt_str = f"2024-01-01T00:00:00"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        assert isinstance(parsed, datetime)
    except (ValueError, dateutil.parser.ParserError):
        pass


@given(st.sampled_from(['AM', 'PM', 'am', 'pm', 'A.M.', 'P.M.', 'a.m.', 'p.m.']),
       st.integers(0, 23))
def test_am_pm_with_24_hour_time(meridiem, hour):
    """Test AM/PM markers with various hour values."""
    time_str = f"{hour:02d}:00:00 {meridiem}"
    
    try:
        parsed = dateutil.parser.parse(time_str)
        assert isinstance(parsed, datetime)
        
        # Check AM/PM logic
        is_pm = meridiem.upper().startswith('P')
        if hour == 0:
            expected_hour = 12 if is_pm else 0
        elif hour <= 12:
            if is_pm and hour != 12:
                expected_hour = hour + 12
            elif not is_pm and hour == 12:
                expected_hour = 0
            else:
                expected_hour = hour
        else:
            # Hour > 12 with AM/PM might be invalid
            pass
            
    except (dateutil.parser.ParserError, ValueError):
        pass


@given(st.sampled_from(['/', '-', '.', ' ', '_']),
       st.integers(1, 12), st.integers(1, 31), st.integers(0, 99))
def test_different_date_separators(sep, month, day, year):
    """Test different date separator characters."""
    date_str = f"{month:02d}{sep}{day:02d}{sep}{year:02d}"
    
    try:
        parsed = dateutil.parser.parse(date_str)
        assert isinstance(parsed, datetime)
    except (dateutil.parser.ParserError, ValueError):
        pass


@given(st.text(alphabet="TZ+-:", min_size=1, max_size=10))
def test_timezone_designator_variations(tz_str):
    """Test various timezone designator formats."""
    dt_str = f"2024-01-01T12:00:00{tz_str}"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        assert isinstance(parsed, datetime)
    except (ValueError, dateutil.parser.ParserError, AttributeError):
        pass


@given(st.lists(st.sampled_from(['2024', '01', '15', '12', '30', '45']), 
                min_size=1, max_size=10))
def test_repeated_components(components):
    """Test strings with repeated date/time components."""
    s = ' '.join(components)
    
    try:
        parsed = dateutil.parser.parse(s)
        assert isinstance(parsed, datetime)
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.integers(1, 12), st.integers(0, 100))
def test_invalid_day_values(month, day):
    """Test handling of invalid day values for given months."""
    date_str = f"2024-{month:02d}-{day:02d}"
    
    try:
        parsed = dateutil.parser.parse(date_str)
        # If it parses with an invalid day, this might be a bug
        from calendar import monthrange
        max_day = monthrange(2024, month)[1]
        if day > max_day or day == 0:
            # This should have failed but didn't - potential bug
            print(f"Unexpected success: parsed {date_str} as {parsed}")
    except (dateutil.parser.ParserError, ValueError):
        # Expected for invalid days
        pass


@given(st.text(alphabet="0123456789-T:.", min_size=1),
       st.booleans(), st.booleans())
def test_parse_with_various_flags(s, fuzzy, dayfirst):
    """Test parse with different flag combinations."""
    try:
        result = dateutil.parser.parse(s, fuzzy=fuzzy, dayfirst=dayfirst)
        assert isinstance(result, datetime)
    except (dateutil.parser.ParserError, ValueError, OverflowError):
        pass


@given(st.sampled_from(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun',
                        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
       st.integers(1, 31), st.integers(1, 12), st.integers(1900, 2100))
def test_weekday_parsing(weekday, day, month, year):
    """Test parsing dates with weekday names."""
    from calendar import monthrange
    max_day = monthrange(year, month)[1]
    assume(day <= max_day)
    
    date_str = f"{weekday}, {day} {month} {year}"
    
    try:
        parsed = dateutil.parser.parse(date_str)
        assert parsed.day == day
        assert parsed.year == year
    except (dateutil.parser.ParserError, ValueError):
        pass


# Special test for empty value edge case
def test_empty_value_bug():
    """Test for potential bug with empty values in parsing."""
    test_cases = [
        "",
        " ",
        "\t",
        "\n",
        "   \t\n   ",
        None
    ]
    
    for value in test_cases:
        if value is None:
            with pytest.raises(TypeError):
                dateutil.parser.parse(value)
        else:
            with pytest.raises(dateutil.parser.ParserError):
                dateutil.parser.parse(value)


if __name__ == "__main__":
    # Run with higher example count to find more bugs
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])