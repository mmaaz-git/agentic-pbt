#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.extractors as extractors
from datetime import datetime
import re

print("Pinpointing the exact bug location...")
print("="*70)

# Test string that triggers the bug
test_string = "2024-04-31"

print(f"Testing: {test_string}")
print()

# Check Step 3 in custom_parse: YMD_PATTERN
print("Step 3 of custom_parse: YMD_PATTERN matching")
print("-"*70)

match = extractors.YMD_PATTERN.search(test_string)
if match:
    print(f"Pattern matched: {match.groups()}")
    print(f"Groups: {match.groupdict()}")
    
    # The code tries to create a datetime
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    
    print(f"Extracted: year={year}, month={month}, day={day}")
    
    # The code then tries to create datetime
    print("\nAttempting datetime creation:")
    try:
        candidate = datetime(year, month, day)
        print(f"  Success: {candidate}")
    except ValueError as e:
        print(f"  ValueError: {e}")
        print("\nBUT THE FUNCTION STILL RETURNS A DATE!")

# Let's look more carefully at the actual implementation
print("\n" + "="*70)
print("Looking at the ACTUAL bug location...")
print("="*70)

# Check YM_PATTERN (Step 4 in custom_parse)
print("\nStep 4 of custom_parse: YM_PATTERN matching")
print("-"*70)

match_ym = extractors.YM_PATTERN.search(test_string)
if match_ym:
    print(f"YM_PATTERN matched: {match_ym.groups()}")
    print(f"Groups: {match_ym.groupdict()}")
    
    # This creates a date with day=1
    if match_ym.lastgroup == "month":
        year = int(match_ym.group("year"))
        month = int(match_ym.group("month"))
        print(f"Would create: datetime({year}, {month}, 1)")
        try:
            candidate = datetime(year, month, 1)
            print(f"Result: {candidate}")
        except ValueError as e:
            print(f"ValueError: {e}")

print("\n" + "="*70)
print("ROOT CAUSE IDENTIFIED!")
print("="*70)

print("""
The bug is in the YM_PATTERN regex and Step 4 of custom_parse:

1. When parsing "2024-04-31", the YMD_PATTERN matches but datetime creation fails
2. The code continues to Step 4 where YM_PATTERN matches "2024-04"
3. YM_PATTERN extracts year=2024, month=04 and creates datetime(2024, 4, 1)
4. This silently discards the invalid day and returns the first of the month!

The YM_PATTERN regex is: {}

It matches the year and month part of invalid dates like "2024-04-31"
and then constructs a valid date with day=1, ignoring the invalid day.
""".format(extractors.YM_PATTERN.pattern))

# Verify this hypothesis
print("\nVerification with more examples:")
print("-"*70)

invalid_dates = [
    "2024-02-30",  # Feb 30
    "2024-04-31",  # April 31
    "2024-06-31",  # June 31
    "2024-12-32",  # Dec 32
    "2024-12-00",  # Day 0
]

for date_str in invalid_dates:
    # Check if YMD fails but YM succeeds
    ymd_match = extractors.YMD_PATTERN.search(date_str)
    ym_match = extractors.YM_PATTERN.search(date_str)
    
    print(f"{date_str}:")
    if ymd_match:
        year, month, day = ymd_match.group("year"), ymd_match.group("month"), ymd_match.group("day")
        print(f"  YMD matches: y={year}, m={month}, d={day}")
        try:
            datetime(int(year), int(month), int(day))
            print(f"  YMD datetime: OK")
        except ValueError:
            print(f"  YMD datetime: FAILS")
    
    if ym_match:
        if ym_match.lastgroup == "month":
            year, month = ym_match.group("year"), ym_match.group("month")
            print(f"  YM matches: y={year}, m={month} -> datetime({year}, {month}, 1)")
            
    result = extractors.custom_parse(date_str, "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31))
    print(f"  Final result: {result}")
    print()