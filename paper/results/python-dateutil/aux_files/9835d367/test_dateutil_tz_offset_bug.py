#!/usr/bin/env python3
"""Test for potential bug in tzical offset parsing"""

import dateutil.tz
from io import StringIO
import pytest

def test_tzical_parse_offset_empty_value_bug():
    """Test that tzical._parse_offset correctly handles empty strings"""
    
    # Create a minimal valid VTIMEZONE structure
    ical_content = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
END:STANDARD
END:VTIMEZONE"""
    
    # Create tzical instance
    tzical = dateutil.tz.tzical(StringIO(ical_content))
    
    # Test 1: Empty string should raise ValueError
    with pytest.raises(ValueError, match="empty offset"):
        tzical._parse_offset("")
    
    # Test 2: Whitespace-only string should also raise ValueError after stripping
    with pytest.raises(ValueError, match="empty offset"):
        tzical._parse_offset("   ")
    
    # Test 3: Tab and newline should also result in empty after stripping
    with pytest.raises(ValueError, match="empty offset"):
        tzical._parse_offset("\t\n")

def test_tzical_parse_offset_invalid_length():
    """Test that tzical._parse_offset handles invalid offset string lengths"""
    
    ical_content = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
END:STANDARD
END:VTIMEZONE"""
    
    tzical = dateutil.tz.tzical(StringIO(ical_content))
    
    # Valid lengths are 4 (HHMM) and 6 (HHMMSS)
    # Test invalid lengths
    
    # Length 0 (after stripping sign) - but this would be caught as "empty offset"
    # Length 1
    with pytest.raises(ValueError, match="invalid offset"):
        tzical._parse_offset("+1")
    
    # Length 2
    with pytest.raises(ValueError, match="invalid offset"):
        tzical._parse_offset("+12")
    
    # Length 3
    with pytest.raises(ValueError, match="invalid offset"):
        tzical._parse_offset("+123")
    
    # Length 5
    with pytest.raises(ValueError, match="invalid offset"):
        tzical._parse_offset("+12345")
    
    # Length 7
    with pytest.raises(ValueError, match="invalid offset"):
        tzical._parse_offset("+1234567")

def test_tzical_parse_rfc_with_invalid_offset():
    """Test that invalid offsets in VTIMEZONE cause proper errors"""
    
    # Test with empty TZOFFSETTO value
    ical_content_empty = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:
END:STANDARD
END:VTIMEZONE"""
    
    # This should raise ValueError when parsing
    with pytest.raises(ValueError, match="empty offset"):
        tzical = dateutil.tz.tzical(StringIO(ical_content_empty))
    
    # Test with whitespace-only TZOFFSETTO value
    ical_content_whitespace = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:   
END:STANDARD
END:VTIMEZONE"""
    
    with pytest.raises(ValueError, match="empty offset"):
        tzical = dateutil.tz.tzical(StringIO(ical_content_whitespace))

if __name__ == "__main__":
    test_tzical_parse_offset_empty_value_bug()
    print("✓ Empty value handling test passed")
    
    test_tzical_parse_offset_invalid_length()
    print("✓ Invalid length handling test passed")
    
    test_tzical_parse_rfc_with_invalid_offset()
    print("✓ Invalid offset in VTIMEZONE test passed")
    
    print("\nAll tests passed!")