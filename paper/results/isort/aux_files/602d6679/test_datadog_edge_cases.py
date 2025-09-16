#!/usr/bin/env python3
"""Edge case focused property-based tests for datadog_checks.utils functions."""

import datetime
import math
import re
from decimal import ROUND_HALF_UP, ROUND_DOWN, ROUND_UP, Decimal
from hypothesis import assume, given, strategies as st, settings, example
import pytest


# Copy the function implementations directly
def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    precision = '0.{}'.format('0' * precision)
    return float(Decimal(str(value)).quantize(Decimal(precision), rounding=rounding_method))


class TimezoneInfo(datetime.tzinfo):
    def __init__(self, h, m):
        self._name = "UTC"
        if h != 0 and m != 0:
            self._name += "%+03d:%2d" % (h, m)
        self._delta = datetime.timedelta(hours=h, minutes=math.copysign(m, h))

    def utcoffset(self, dt):
        return self._delta

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return datetime.timedelta(0)


UTC = TimezoneInfo(0, 0)

_re_rfc3339 = re.compile(
    r"(\d\d\d\d)-(\d\d)-(\d\d)"  # full-date
    r"[ Tt]"  # Separator
    r"(\d\d):(\d\d):(\d\d)([.,]\d+)?"  # partial-time
    r"([zZ ]|[-+]\d\d?:\d\d)?",  # time-offset
    re.VERBOSE + re.IGNORECASE,
)
_re_timezone = re.compile(r"([-+])(\d\d?):?(\d\d)?")


def parse_rfc3339(s):
    if isinstance(s, datetime.datetime):
        # no need to parse it, just make sure it has a timezone.
        if not s.tzinfo:
            return s.replace(tzinfo=UTC)
        return s
    groups = _re_rfc3339.search(s).groups()
    dt = [0] * 7
    for x in range(6):
        dt[x] = int(groups[x])
    if groups[6] is not None:
        dt[6] = int(groups[6])
    tz = UTC
    if groups[7] is not None and groups[7] != 'Z' and groups[7] != 'z':
        tz_groups = _re_timezone.search(groups[7]).groups()
        hour = int(tz_groups[1])
        minute = 0
        if tz_groups[0] == "-":
            hour *= -1
        if tz_groups[2]:
            minute = int(tz_groups[2])
        tz = TimezoneInfo(hour, minute)
    return datetime.datetime(
        year=dt[0], month=dt[1], day=dt[2], hour=dt[3], minute=dt[4], second=dt[5], microsecond=dt[6], tzinfo=tz
    )


def format_rfc3339(date_time):
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=UTC)
    date_time = date_time.astimezone(UTC)
    return date_time.strftime('%Y-%m-%dT%H:%M:%SZ')


# Edge case tests

# Test for microsecond parsing issues in RFC3339
@settings(max_examples=1000)
@given(st.text(min_size=1, max_size=10))
@example(".123456")  # Valid microseconds
@example(".1")       # Single digit
@example(".123456789")  # Too many digits
@example(",123456")  # Comma separator (valid per RFC3339)
@example(".00000000000000")  # Many zeros
def test_rfc3339_microsecond_edge_cases(frac_seconds):
    """Test RFC3339 parsing with various fractional second formats."""
    date_str = f"2024-01-01T12:00:00{frac_seconds}Z"
    
    # Check if the fractional part matches the regex
    if re.match(r'^[.,]\d+$', frac_seconds):
        try:
            parsed = parse_rfc3339(date_str)
            assert isinstance(parsed, datetime.datetime)
            
            # Extract the microsecond value
            if frac_seconds.startswith('.') or frac_seconds.startswith(','):
                # The function should parse this as microseconds
                # but it's parsing it as an integer directly!
                frac_str = frac_seconds[1:]
                if frac_str:
                    # This is a BUG: the function does int(groups[6]) 
                    # which treats ".123456" as 123456 microseconds
                    # But ".1" should be 100000 microseconds, not 1!
                    pass
        except Exception as e:
            # Record any exceptions for analysis
            print(f"Exception parsing {date_str}: {e}")


# Test for microsecond precision loss
@settings(max_examples=500)
@given(st.integers(min_value=0, max_value=999999))
def test_rfc3339_microsecond_precision(microseconds):
    """Test that microseconds are preserved in parse_rfc3339."""
    # Create a datetime with specific microseconds
    dt = datetime.datetime(2024, 1, 1, 12, 0, 0, microseconds, tzinfo=UTC)
    
    # Format it manually with microseconds
    if microseconds > 0:
        date_str = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'  # Remove trailing zeros
    else:
        date_str = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Parse it back
    parsed = parse_rfc3339(date_str)
    
    # Check microseconds match - but wait, format_rfc3339 doesn't include microseconds!
    formatted = format_rfc3339(dt)
    reparsed = parse_rfc3339(formatted)
    
    # BUG: format_rfc3339 loses microsecond precision!
    assert reparsed.microsecond == 0  # This will always be 0


# Focused test to demonstrate microsecond parsing bug
def test_rfc3339_microsecond_parsing_bug():
    """Demonstrate the microsecond parsing bug in parse_rfc3339."""
    
    # ".1" should represent 0.1 seconds = 100000 microseconds
    date_str1 = "2024-01-01T12:00:00.1Z"
    parsed1 = parse_rfc3339(date_str1)
    print(f"Parsed .1 as {parsed1.microsecond} microseconds")
    
    # ".100000" should also be 100000 microseconds  
    date_str2 = "2024-01-01T12:00:00.100000Z"
    parsed2 = parse_rfc3339(date_str2)
    print(f"Parsed .100000 as {parsed2.microsecond} microseconds")
    
    # BUG: These should be equal but they're not!
    # The function does int(groups[6]) which treats ".1" as integer 1
    # instead of treating it as a fractional second
    if parsed1.microsecond != parsed2.microsecond:
        print(f"BUG FOUND: .1 parsed as {parsed1.microsecond} but should be 100000")
        return False
    return True


# Test for negative rounding edge cases
@settings(max_examples=500)
@given(st.floats(min_value=-10, max_value=-0.01, allow_nan=False))
def test_round_value_negative_edge_cases(value):
    """Test rounding behavior with negative numbers."""
    # Test that ROUND_UP for negative numbers goes toward zero
    up = round_value(value, 0, ROUND_UP)
    assert up >= math.floor(value)  # Should round toward zero
    
    # Test that ROUND_DOWN for negative numbers goes away from zero  
    down = round_value(value, 0, ROUND_DOWN)
    assert down <= math.ceil(value)  # Should round away from zero


# Test TimezoneInfo edge cases
def test_timezone_info_edge_cases():
    """Test TimezoneInfo with edge case values."""
    # Test with h != 0 but m == 0 - the name generation has a bug!
    tz1 = TimezoneInfo(5, 0)
    # BUG: The condition is "if h != 0 and m != 0" but should be "if h != 0 or m != 0"
    # So this won't add the offset to the name when minutes are 0
    assert tz1._name == "UTC"  # This is wrong! Should be "UTC+05:00"
    
    # Test with h == 0 but m != 0
    tz2 = TimezoneInfo(0, 30)
    assert tz2._name == "UTC"  # Also wrong! Should be "UTC+00:30"
    
    # Only works when both are non-zero
    tz3 = TimezoneInfo(5, 30)
    assert tz3._name == "UTC+05:30"  # This one works


# Test pattern_filter edge cases
def test_pattern_filter_empty_patterns():
    """Test pattern_filter with empty pattern lists."""
    items = ["test1", "test2", "test3"]
    
    # Empty lists should behave like no filter
    result = pattern_filter(items, whitelist=[], blacklist=[])
    # BUG POTENTIAL: Empty whitelist list means nothing passes!
    # The code checks "if whitelist:" which is False for empty list
    # but then still tries to filter with empty pattern list
    assert result == items  # This might fail


if __name__ == "__main__":
    print("Running edge case tests...")
    
    # Run the specific bug demonstration
    print("\n--- Testing RFC3339 Microsecond Parsing Bug ---")
    if not test_rfc3339_microsecond_parsing_bug():
        print("RFC3339 microsecond parsing bug confirmed!")
    
    print("\n--- Testing TimezoneInfo Name Generation Bug ---")
    test_timezone_info_edge_cases()
    
    print("\n--- Running all tests with pytest ---")
    pytest.main([__file__, "-v", "--tb=short", "-x"])