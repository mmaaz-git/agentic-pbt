#!/usr/bin/env python3
"""Property-based testing for tzical._parse_offset to find bugs"""

from hypothesis import given, strategies as st, assume, settings
import dateutil.tz
from io import StringIO
import pytest

# Create a reusable tzical instance
def get_tzical():
    ical_content = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
END:STANDARD
END:VTIMEZONE"""
    return dateutil.tz.tzical(StringIO(ical_content))

# Property: parse_offset should handle various string inputs correctly
@given(st.text(min_size=0, max_size=10))
@settings(max_examples=1000)
def test_parse_offset_fuzzing(s):
    """Fuzz test parse_offset with various strings"""
    tzical = get_tzical()
    
    try:
        result = tzical._parse_offset(s)
        # If it succeeds, verify the result makes sense
        # Offset should be in seconds and within reasonable bounds
        # Maximum offset is ±14 hours = ±50400 seconds (for Kiribati)
        # But let's be generous and allow ±24 hours = ±86400 seconds
        assert isinstance(result, int)
        assert -86400 <= result <= 86400, f"Offset {result} seconds is unreasonable"
    except ValueError as e:
        # ValueError is expected for invalid inputs
        # Check that the error message makes sense
        error_msg = str(e)
        assert any(phrase in error_msg for phrase in ["empty offset", "invalid offset"]), \
            f"Unexpected error message: {error_msg}"
    except Exception as e:
        # Any other exception could be a bug
        pytest.fail(f"Unexpected exception {type(e).__name__}: {e} for input '{s}'")

# Property: Valid offset formats should parse correctly
@given(
    sign=st.sampled_from(['+', '-', '']),
    hours=st.integers(min_value=0, max_value=23),
    minutes=st.integers(min_value=0, max_value=59),
    seconds=st.integers(min_value=0, max_value=59),
    format_type=st.sampled_from(['HHMM', 'HHMMSS'])
)
def test_parse_offset_valid_formats(sign, hours, minutes, seconds, format_type):
    """Test that valid offset formats parse correctly"""
    tzical = get_tzical()
    
    # Construct the offset string
    if format_type == 'HHMM':
        offset_str = f"{sign}{hours:02d}{minutes:02d}"
        expected_seconds = hours * 3600 + minutes * 60
    else:  # HHMMSS
        offset_str = f"{sign}{hours:02d}{minutes:02d}{seconds:02d}"
        expected_seconds = hours * 3600 + minutes * 60 + seconds
    
    # Apply sign
    if sign == '-':
        expected_seconds = -expected_seconds
    elif sign == '':
        # No sign means positive
        expected_seconds = abs(expected_seconds)
    
    result = tzical._parse_offset(offset_str)
    assert result == expected_seconds, f"Parse failed for '{offset_str}': got {result}, expected {expected_seconds}"

# Property: parse_offset should handle edge case numeric values
@given(st.text(alphabet='0123456789+-', min_size=1, max_size=8))
def test_parse_offset_numeric_strings(s):
    """Test parse_offset with strings containing only numbers and signs"""
    tzical = get_tzical()
    
    try:
        result = tzical._parse_offset(s)
        # Verify the result is reasonable
        assert isinstance(result, int)
        assert -86400 <= result <= 86400
    except ValueError:
        # Expected for invalid formats
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception for numeric string '{s}': {e}")

# Property: Whitespace handling
@given(
    leading_space=st.text(alphabet=' \t\n\r', min_size=0, max_size=5),
    trailing_space=st.text(alphabet=' \t\n\r', min_size=0, max_size=5),
    middle_content=st.text(min_size=0, max_size=6)
)
def test_parse_offset_whitespace_handling(leading_space, trailing_space, middle_content):
    """Test that whitespace is handled correctly"""
    tzical = get_tzical()
    
    # Create string with leading and trailing whitespace
    s = leading_space + middle_content + trailing_space
    
    try:
        result = tzical._parse_offset(s)
        # If successful, the middle content should have been valid after stripping
        stripped = middle_content.strip()
        # Re-parse the stripped version to verify consistency
        result2 = tzical._parse_offset(stripped)
        assert result == result2, f"Inconsistent parsing with/without whitespace"
    except ValueError as e:
        # Check that stripped version also fails
        try:
            tzical._parse_offset(middle_content.strip())
            # If this succeeds but the original failed, that's inconsistent
            pytest.fail(f"Whitespace handling inconsistent: '{s}' failed but '{middle_content.strip()}' succeeded")
        except ValueError:
            # Both fail, which is consistent
            pass

# Property: Non-ASCII characters should be rejected
@given(st.text(min_size=1, max_size=10).filter(lambda x: any(ord(c) > 127 for c in x)))
def test_parse_offset_non_ascii(s):
    """Test that non-ASCII characters are properly rejected"""
    tzical = get_tzical()
    
    try:
        result = tzical._parse_offset(s)
        # If this succeeds with non-ASCII, might be a bug
        # Unless the non-ASCII is just in whitespace that gets stripped
        if any(ord(c) > 127 for c in s.strip()):
            pytest.fail(f"parse_offset accepted non-ASCII string: '{s}'")
    except (ValueError, UnicodeError):
        # Expected
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception for non-ASCII string: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])