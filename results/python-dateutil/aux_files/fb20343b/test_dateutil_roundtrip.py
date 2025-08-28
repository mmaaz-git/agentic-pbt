"""
Test round-trip properties and format compatibility in dateutil.parser.
"""
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, assume, settings, example
import dateutil.parser
import dateutil.tz
import pytest


# Test round-trip with timezones
@given(st.integers(-12, 14), st.integers(0, 59))
def test_timezone_offset_roundtrip(hours, minutes):
    """Test round-trip parsing of timezone offsets."""
    # Create a timezone offset
    total_minutes = hours * 60 + (minutes if hours >= 0 else -minutes)
    
    # Skip invalid offsets
    if abs(total_minutes) > 24 * 60:
        return
    
    tz = timezone(timedelta(minutes=total_minutes))
    dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=tz)
    
    # Convert to ISO format and parse back
    iso_str = dt.isoformat()
    parsed = dateutil.parser.isoparse(iso_str)
    
    assert parsed == dt, f"Round-trip failed for timezone offset {hours}:{minutes:02d}"


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_parse_isoformat_roundtrip(dt):
    """Test that parse() can handle isoformat() output."""
    iso_str = dt.isoformat()
    parsed = dateutil.parser.parse(iso_str)  # Using parse instead of isoparse
    assert parsed == dt


@given(st.integers(0, 999999))
def test_microsecond_roundtrip(microseconds):
    """Test round-trip of microseconds."""
    dt = datetime(2024, 1, 1, 0, 0, 0, microseconds)
    iso_str = dt.isoformat()
    parsed = dateutil.parser.isoparse(iso_str)
    assert parsed.microsecond == microseconds


@given(st.floats(min_value=0, max_value=0.999999, allow_nan=False))
def test_fractional_second_roundtrip(fraction):
    """Test round-trip of fractional seconds."""
    # Convert fraction to microseconds
    microseconds = int(fraction * 1000000)
    dt = datetime(2024, 1, 1, 0, 0, 0, microseconds)
    
    # Format with fractional seconds
    iso_str = dt.isoformat()
    parsed = dateutil.parser.isoparse(iso_str)
    
    # Check microseconds match (within precision limits)
    assert abs(parsed.microsecond - microseconds) <= 1


@given(st.sampled_from(['T', 't', ' ']), st.booleans())
def test_datetime_separator_variations(separator, use_isoparse):
    """Test different date-time separators."""
    dt_str = f"2024-01-15{separator}12:30:45"
    
    try:
        if use_isoparse:
            parsed = dateutil.parser.isoparse(dt_str)
        else:
            parsed = dateutil.parser.parse(dt_str)
        
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 12
        assert parsed.minute == 30
        assert parsed.second == 45
    except (ValueError, dateutil.parser.ParserError):
        # Space separator might not work with isoparse
        if separator == ' ' and use_isoparse:
            pass  # Expected
        else:
            raise


@given(st.datetimes(), st.sampled_from([True, False, None]))
def test_fuzzy_with_datetime_string(dt, fuzzy):
    """Test fuzzy parsing with datetime strings."""
    # Embed datetime in text
    text = f"The meeting is on {dt} in the conference room"
    
    kwargs = {} if fuzzy is None else {'fuzzy': fuzzy}
    
    try:
        parsed = dateutil.parser.parse(text, **kwargs)
        if fuzzy or fuzzy is None:
            # Should extract the datetime
            assert parsed == dt
    except dateutil.parser.ParserError:
        # Should fail without fuzzy=True
        assert fuzzy is False or fuzzy is None


@given(st.integers(1, 9999), st.integers(1, 53))
def test_week_number_formats(year, week):
    """Test week number format variations."""
    # ISO week date format
    for day in range(1, 8):
        week_str = f"{year:04d}-W{week:02d}-{day}"
        compact_str = f"{year:04d}W{week:02d}{day}"
        
        for s in [week_str, compact_str]:
            try:
                parsed = dateutil.parser.isoparse(s)
                assert isinstance(parsed, datetime)
            except (ValueError, dateutil.parser.ParserError, AttributeError):
                pass


# Property: Parsing the same string twice should give the same result
@given(st.text(min_size=1, max_size=50))
def test_parse_deterministic(s):
    """Test that parsing is deterministic."""
    results = []
    errors = []
    
    for _ in range(3):
        try:
            result = dateutil.parser.parse(s, fuzzy=True)
            results.append(result)
        except Exception as e:
            errors.append(type(e).__name__)
    
    if results:
        # All successful parses should give the same result
        assert all(r == results[0] for r in results)
    else:
        # All should fail with the same error type
        assert all(e == errors[0] for e in errors)


@given(st.integers(1, 12), st.integers(1, 31), st.integers(0, 99))
def test_ambiguous_format_consistency(month, day, year):
    """Test consistency in parsing ambiguous date formats."""
    # Skip invalid dates
    from calendar import monthrange
    if month == 2:
        max_day = 29
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:
        max_day = 31
    assume(day <= max_day)
    
    # Different orderings that could be ambiguous
    formats = [
        f"{month:02d}-{day:02d}-{year:02d}",  # MM-DD-YY
        f"{month:02d}/{day:02d}/{year:02d}",  # MM/DD/YY
        f"{day:02d}-{month:02d}-{year:02d}",  # DD-MM-YY
        f"{day:02d}/{month:02d}/{year:02d}",  # DD/MM/YY
    ]
    
    for fmt in formats:
        try:
            parsed = dateutil.parser.parse(fmt)
            # Should successfully parse to some date
            assert isinstance(parsed, datetime)
        except dateutil.parser.ParserError:
            pass


# Test for potential infinite loops or hangs
@given(st.text(alphabet="0123456789-+:TZ.", max_size=1000))
@settings(max_examples=100)  # Limit examples
def test_no_infinite_loops(s):
    """Test that parser doesn't hang on any input."""
    try:
        dateutil.parser.parse(s)
    except:
        pass  # Any exception is fine, we just don't want hangs


# Look for format injection or special character issues
@given(st.text(alphabet="\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f", min_size=1))
def test_control_characters(s):
    """Test handling of control characters."""
    try:
        result = dateutil.parser.parse(s)
        # If it parses control characters, that might be unexpected
        print(f"Parsed control characters: {repr(s)} -> {result}")
    except:
        pass  # Expected to fail


@given(st.lists(st.sampled_from(['2024', '-', '01', '-', '15']), min_size=5, max_size=50))
def test_repeated_separators(components):
    """Test strings with repeated separators."""
    s = ''.join(components)
    
    # Count consecutive separators
    max_consecutive = 0
    current = 0
    for c in s:
        if c == '-':
            current += 1
            max_consecutive = max(max_consecutive, current)
        else:
            current = 0
    
    try:
        parsed = dateutil.parser.parse(s)
        # Multiple consecutive separators might cause issues
        if max_consecutive > 2:
            print(f"Parsed with {max_consecutive} consecutive separators: {s} -> {parsed}")
    except (ValueError, dateutil.parser.ParserError):
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=line", "-x"])