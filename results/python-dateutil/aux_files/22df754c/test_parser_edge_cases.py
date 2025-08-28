import datetime
from hypothesis import given, strategies as st, assume, settings, note
from dateutil import parser
import pytest


# Test parser with year edge cases
@given(st.integers(min_value=0, max_value=99))
def test_parser_two_digit_year(year):
    """Test how parser handles two-digit years"""
    year_str = f"{year:02d}/01/01"
    
    parsed = parser.parse(year_str)
    
    # Two-digit years should be interpreted with a pivot
    # Default pivot seems to be around 1970-2069
    if year >= 70:
        expected_year = 1900 + year
    else:
        expected_year = 2000 + year
    
    assert parsed.year == expected_year


# Test empty/whitespace input
@given(st.text(alphabet=" \t\n\r", min_size=0, max_size=10))
def test_parser_whitespace_input(text):
    """Test parser with whitespace-only input"""
    if not text.strip():
        with pytest.raises(parser.ParserError):
            parser.parse(text)


# Test parser with very large years
@given(st.integers(min_value=10000, max_value=999999))
def test_parser_large_year(year):
    """Test parser with years beyond 9999"""
    date_str = f"{year}-01-01"
    
    try:
        parsed = parser.parse(date_str)
        # Python datetime only supports years 1-9999
        assert False, "Should not parse years > 9999"
    except (ValueError, parser.ParserError, OverflowError):
        # Expected - datetime can't handle years > 9999
        pass


# Test parser with invalid day/month combinations
@given(
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=29, max_value=31)
)
def test_parser_invalid_day_month_combo(month, day):
    """Test parser with potentially invalid day/month combinations"""
    year = 2021  # Non-leap year
    date_str = f"{year}-{month:02d}-{day:02d}"
    
    # Check if this is a valid date
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    
    if day > max_day:
        # This should fail
        with pytest.raises((ValueError, parser.ParserError)):
            parser.parse(date_str)
    else:
        # Should parse successfully
        parsed = parser.parse(date_str)
        assert parsed.year == year
        assert parsed.month == month
        assert parsed.day == day


# Test parser with mixed format strings
@given(st.text(min_size=1, max_size=50))
def test_parser_fuzzy_extraction(text):
    """Test fuzzy parser extracts dates from text"""
    # Add a known date to random text
    text_with_date = f"Random {text} 2020-06-15 more text"
    
    try:
        result = parser.parse(text_with_date, fuzzy=True)
        # Should extract the date
        assert result.year == 2020
        assert result.month == 6
        assert result.day == 15
    except (parser.ParserError, ValueError, OverflowError):
        # Some text might confuse the parser
        pass


# Test parser with repeated date components
def test_parser_repeated_components():
    """Test parser with repeated date components"""
    # Multiple year specifications
    conflicting_dates = [
        "2020-2021-01-01",  # Two years
        "01-01-01-2020",    # Ambiguous
        "Jan Jan 2020",     # Repeated month
        "Monday Tuesday 2020-01-01",  # Multiple weekdays
    ]
    
    for date_str in conflicting_dates:
        try:
            result = parser.parse(date_str)
            # If it parses, it picked one interpretation
            assert isinstance(result, datetime.datetime)
        except parser.ParserError:
            # This is also acceptable
            pass


# Test isoparse with incomplete dates
@given(st.integers(min_value=1, max_value=9999))
def test_isoparse_year_only(year):
    """Test isoparse with year-only string"""
    year_str = f"{year:04d}"
    
    # isoparse should handle YYYY format
    try:
        parsed = parser.isoparse(year_str)
        assert parsed.year == year
        assert parsed.month == 1
        assert parsed.day == 1
    except ValueError:
        # Some versions might not support year-only
        pass


# Test parser with negative years
def test_parser_negative_year():
    """Test parser with negative years (BCE dates)"""
    date_strings = [
        "-0001-01-01",
        "-100-01-01",
    ]
    
    for date_str in date_strings:
        try:
            parsed = parser.parse(date_str)
            # Python datetime doesn't support negative years
            assert False, "Should not parse negative years"
        except (ValueError, parser.ParserError):
            # Expected
            pass


# Test parser timezone abbreviations
@given(st.sampled_from(["EST", "PST", "UTC", "GMT", "CST", "MST"]))
def test_parser_timezone_abbrev(tz_abbrev):
    """Test parser with timezone abbreviations"""
    date_str = f"2020-06-15 12:00:00 {tz_abbrev}"
    
    try:
        parsed = parser.parse(date_str)
        # Should parse with timezone info
        if tz_abbrev in ["UTC", "GMT"]:
            assert parsed.tzinfo is not None
    except parser.ParserError:
        # Some abbreviations might not be recognized
        pass


# Test microsecond precision
@given(st.integers(min_value=0, max_value=999999))
def test_parser_microsecond_precision(microseconds):
    """Test parser preserves microsecond precision"""
    # Format with 6 digits for microseconds
    date_str = f"2020-06-15T12:00:00.{microseconds:06d}"
    
    parsed = parser.parse(date_str)
    assert parsed.microsecond == microseconds
    
    # Also test isoparse
    iso_parsed = parser.isoparse(date_str)
    assert iso_parsed.microsecond == microseconds


# Test parser with Unicode characters
@given(st.text(min_size=1, max_size=20))
def test_parser_unicode_handling(text):
    """Test parser handles Unicode in fuzzy mode"""
    # Mix unicode with a date
    text_with_date = f"{text} 2020-06-15 {text}"
    
    try:
        result = parser.parse(text_with_date, fuzzy=True)
        assert result.year == 2020
        assert result.month == 6
        assert result.day == 15
    except (parser.ParserError, ValueError, UnicodeError):
        # Some unicode might cause issues
        pass


# Test parser with very long input
def test_parser_long_input():
    """Test parser with very long input strings"""
    # Create a very long string with a date in the middle
    long_text = "x" * 10000 + " 2020-06-15 " + "y" * 10000
    
    try:
        result = parser.parse(long_text, fuzzy=True)
        assert result.year == 2020
        assert result.month == 6
        assert result.day == 15
    except parser.ParserError:
        # Might fail on very long input
        pass


# Test parser default parameter edge case
def test_parser_default_override():
    """Test parser default parameter with partial dates"""
    default = datetime.datetime(1999, 12, 31, 23, 59, 59)
    
    # Parse just a time
    result = parser.parse("14:30", default=default)
    assert result.year == 1999
    assert result.month == 12
    assert result.day == 31
    assert result.hour == 14
    assert result.minute == 30
    assert result.second == 0  # Seconds get reset to 0, not default!
    
    # Parse just a date
    result = parser.parse("2020-06-15", default=default)
    assert result.year == 2020
    assert result.month == 6
    assert result.day == 15
    assert result.hour == 0  # Time gets reset to 00:00:00, not default!
    assert result.minute == 0
    assert result.second == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])