"""
Focused property-based tests to find real bugs in dateutil.parser.
"""
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, assume, settings, seed
import dateutil.parser
import pytest


# Test for actual parsing bugs with edge cases
@given(st.integers(0, 999999999))
def test_microsecond_overflow(microseconds):
    """Test that microseconds beyond valid range are handled correctly."""
    # datetime only supports microseconds up to 999999
    dt_str = f"2024-01-01T00:00:00.{microseconds:09d}"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        # Microseconds should be clamped or raise an error if > 999999
        assert 0 <= parsed.microsecond <= 999999
    except (ValueError, dateutil.parser.ParserError):
        # Should raise for invalid microseconds
        pass


@given(st.integers(0, 99), st.integers(0, 99), st.integers(0, 99))
def test_ambiguous_date_components(a, b, c):
    """Test parsing of ambiguous date strings like '01-02-03'."""
    date_str = f"{a:02d}-{b:02d}-{c:02d}"
    
    try:
        parsed = dateutil.parser.parse(date_str)
        # Check that the result is reasonable
        assert isinstance(parsed, datetime)
        assert 1 <= parsed.month <= 12
        assert 1 <= parsed.day <= 31
    except (ValueError, dateutil.parser.ParserError):
        pass


@given(st.integers(24, 99), st.integers(0, 59), st.integers(0, 59))
def test_invalid_hour_values(hour, minute, second):
    """Test handling of invalid hour values (>23)."""
    time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
    
    # This should either fail or interpret the hour differently
    try:
        parsed = dateutil.parser.parse(time_str)
        # If it parses an hour > 23, this might be unexpected
        if hour > 23:
            print(f"Parsed hour {hour} as: {parsed}")
    except (ValueError, dateutil.parser.ParserError):
        pass  # Expected for invalid hours


@given(st.integers(60, 99), st.integers(0, 59))
def test_invalid_minute_values(minute, second):
    """Test handling of invalid minute values (>59)."""
    time_str = f"12:{minute:02d}:{second:02d}"
    
    # This should fail for minutes >= 60
    try:
        parsed = dateutil.parser.parse(time_str)
        # If it successfully parses minute >= 60, this is likely a bug
        print(f"WARNING: Parsed minute {minute} as: {parsed}")
    except (ValueError, dateutil.parser.ParserError):
        pass  # Expected


@given(st.integers(60, 99))
def test_invalid_second_values(second):
    """Test handling of invalid second values (>59)."""
    time_str = f"12:00:{second:02d}"
    
    # This should fail for seconds >= 60 (except maybe 60 for leap seconds?)
    try:
        parsed = dateutil.parser.parse(time_str)
        # Seconds >= 61 should definitely fail
        if second >= 61:
            print(f"WARNING: Parsed second {second} as: {parsed}")
    except (ValueError, dateutil.parser.ParserError):
        pass  # Expected


@given(st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_special_float_values(value):
    """Test handling of special float values."""
    try:
        # Try as string
        result = dateutil.parser.parse(str(value))
        print(f"Unexpectedly parsed {value} as {result}")
    except (ValueError, dateutil.parser.ParserError, OverflowError):
        pass  # Expected


@given(st.text(alphabet="0123456789", min_size=20, max_size=50))
def test_very_long_numeric_strings(s):
    """Test parsing very long numeric strings."""
    try:
        result = dateutil.parser.parse(s)
        # Long numeric strings might overflow or be misinterpreted
        assert isinstance(result, datetime)
    except (ValueError, dateutil.parser.ParserError, OverflowError):
        pass


@given(st.integers(0, 9999))
def test_year_edge_cases(year):
    """Test edge cases around year boundaries."""
    # Test year 0 (should fail)
    if year == 0:
        with pytest.raises((ValueError, dateutil.parser.ParserError)):
            dateutil.parser.parse(f"{year:04d}-01-01")
        return
    
    date_str = f"{year:04d}-01-01"
    parsed = dateutil.parser.parse(date_str)
    assert parsed.year == year


@given(st.sampled_from(['Z', 'z', '+00:00', '-00:00', '+0000', '-0000', 'UTC', 'GMT']))
def test_utc_variations(utc_str):
    """Test different ways to specify UTC."""
    dt_str = f"2024-01-01T12:00:00{utc_str}"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        if parsed.tzinfo is not None:
            # Should be UTC
            offset = parsed.tzinfo.utcoffset(parsed)
            if offset is not None:
                assert offset == timedelta(0), f"Non-zero UTC offset for {utc_str}"
    except (ValueError, dateutil.parser.ParserError, AttributeError):
        pass


@given(st.floats(min_value=0.0, max_value=1.0, exclude_min=False, exclude_max=False))
def test_fractional_seconds_precision(fraction):
    """Test precision handling in fractional seconds."""
    # Create a fractional second with many decimal places
    frac_str = f"{fraction:.15f}".rstrip('0').rstrip('.')
    if '.' in frac_str:
        decimal_part = frac_str.split('.')[1]
        # Microseconds can only handle 6 decimal places
        dt_str = f"2024-01-01T00:00:00.{decimal_part}"
        
        try:
            parsed = dateutil.parser.isoparse(dt_str)
            # Check if precision was preserved correctly (up to 6 digits)
            expected_micro = int((decimal_part + '000000')[:6])
            assert parsed.microsecond == expected_micro
        except (ValueError, dateutil.parser.ParserError):
            pass


@given(st.sampled_from(['', ' ', None]))
def test_empty_default_parameter(empty_val):
    """Test using empty/None values as default parameter."""
    try:
        if empty_val is None:
            # This should work - None is a valid default
            result = dateutil.parser.parse("10:30", default=None)
            # Without a default, this might fail or use system defaults
        else:
            # Empty string as default should fail
            result = dateutil.parser.parse("10:30", default=empty_val)
    except (TypeError, AttributeError, ValueError, dateutil.parser.ParserError):
        pass


@given(st.sampled_from([
    '2024-02-30',  # Invalid: Feb 30
    '2024-04-31',  # Invalid: Apr 31
    '2024-06-31',  # Invalid: Jun 31
    '2024-09-31',  # Invalid: Sep 31
    '2024-11-31',  # Invalid: Nov 31
    '2023-02-29',  # Invalid: Feb 29 in non-leap year
]))
def test_invalid_dates(date_str):
    """Test parsing of invalid calendar dates."""
    # These should all raise errors
    with pytest.raises((ValueError, dateutil.parser.ParserError)):
        dateutil.parser.parse(date_str)


@given(st.integers(13, 99), st.sampled_from(['AM', 'PM', 'am', 'pm']))
def test_invalid_12hour_times(hour, meridiem):
    """Test invalid hour values with AM/PM."""
    time_str = f"{hour}:00 {meridiem}"
    
    # Hours > 12 with AM/PM should fail
    try:
        parsed = dateutil.parser.parse(time_str)
        # This might be a bug if it accepts hour > 12 with AM/PM
        print(f"Accepted invalid 12-hour time: {time_str} -> {parsed}")
    except (ValueError, dateutil.parser.ParserError):
        pass  # Expected


@given(st.text(alphabet="0123456789-:T", min_size=1).filter(lambda x: 'T' in x))
def test_iso_format_with_missing_components(s):
    """Test ISO format strings with missing components."""
    try:
        parsed = dateutil.parser.isoparse(s)
        # Verify it's a valid datetime
        assert isinstance(parsed, datetime)
    except (ValueError, dateutil.parser.ParserError, AttributeError):
        pass


@given(st.integers(-999, -1))
def test_negative_components(value):
    """Test negative values in date/time components."""
    test_cases = [
        f"{value}-01-01",  # Negative year
        f"2024-{value}-01",  # Negative month
        f"2024-01-{value}",  # Negative day
        f"{value}:00:00",  # Negative hour
        f"12:{value}:00",  # Negative minute
        f"12:00:{value}",  # Negative second
    ]
    
    for test_str in test_cases:
        try:
            parsed = dateutil.parser.parse(test_str)
            # Negative components should generally fail
            if value < 0:
                print(f"Accepted negative component: {test_str} -> {parsed}")
        except (ValueError, dateutil.parser.ParserError, OverflowError):
            pass  # Expected


# More focused test on potential round-trip failures
@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_str_repr_round_trip(dt):
    """Test that str() representation can be parsed back."""
    dt_str = str(dt)
    parsed = dateutil.parser.parse(dt_str)
    assert parsed == dt, f"Round-trip failed: {dt} -> {dt_str} -> {parsed}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])