#!/usr/bin/env python3
"""Reproduce bugs in dateutil.tz.tzical._parse_offset"""

import dateutil.tz
from io import StringIO

def create_tzical():
    """Helper to create a tzical instance for testing"""
    ical_content = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
END:STANDARD
END:VTIMEZONE"""
    return dateutil.tz.tzical(StringIO(ical_content))

# Bug 1: Invalid input causes unhelpful ValueError
print("Bug 1: Unhelpful error message for malformed input")
print("=" * 50)
tzical = create_tzical()
try:
    result = tzical._parse_offset("000:")
    print(f"ERROR: Should have raised ValueError, got {result}")
except ValueError as e:
    print(f"Input: '000:'")
    print(f"Error: {e}")
    print(f"Problem: The error 'invalid literal for int()' is not user-friendly")
    print(f"Expected: 'invalid offset: 000:'")

print("\n")

# Bug 2: No validation of hour/minute bounds
print("Bug 2: Accepts invalid hour/minute values")
print("=" * 50)

test_cases = [
    ("2401", "24 hours 01 minute - hours should be 0-23"),
    ("0099", "00 hours 99 minutes - minutes should be 0-59"),
    ("9999", "99 hours 99 minutes - completely invalid"),
    ("2500", "25 hours 00 minutes - hours out of range"),
]

for offset_str, description in test_cases:
    tzical = create_tzical()
    try:
        result = tzical._parse_offset(offset_str)
        hours = result // 3600
        minutes = (result % 3600) // 60
        print(f"Input: '{offset_str}' ({description})")
        print(f"  ACCEPTED as {result} seconds = {hours}h {minutes}m")
        print(f"  This is INVALID - should have been rejected!")
    except ValueError as e:
        print(f"Input: '{offset_str}' - Correctly rejected: {e}")
    print()

print("\nSummary:")
print("1. _parse_offset doesn't validate that hours are in range [0-23]")
print("2. _parse_offset doesn't validate that minutes are in range [0-59]")
print("3. Error messages for malformed input are not user-friendly")