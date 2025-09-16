#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.extractors as extractors
from datetime import datetime

print("Testing custom_parse function with edge cases...")
print("="*60)

# Test YYYYMMDD parsing
test_cases = [
    # (input, outputformat, min_date, max_date, expected_behavior)
    ("20240229", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "valid-leap"),  # Feb 29 in leap year
    ("20230229", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-leap"),  # Feb 29 in non-leap year
    ("20240431", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-april-31"),  # April 31 doesn't exist
    ("20240000", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-month-0"),
    ("20241301", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-month-13"),
    ("20240100", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-day-0"),
    ("20240132", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-day-32"),
    ("99991231", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "out-of-range-year"),
    ("20240631", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-june-31"),  # June has 30 days
    ("20240931", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-sept-31"),  # September has 30 days
    ("20241131", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31), "invalid-nov-31"),  # November has 30 days
]

for test_input, fmt, min_date, max_date, desc in test_cases:
    result = extractors.custom_parse(test_input, fmt, min_date, max_date)
    print(f"{desc:20} input={test_input} -> {result}")

print("\n" + "="*60)
print("Testing YMD_PATTERN regex with various inputs...")
print("="*60)

ymd_test_strings = [
    "2024-02-29",  # Valid leap year
    "2023-02-29",  # Invalid leap year
    "2024-04-31",  # Invalid date
    "2024-00-15",  # Month = 0
    "2024-13-01",  # Month > 12
    "2024-12-00",  # Day = 0
    "2024-12-32",  # Day > 31
    "31-12-2024",  # D-M-Y format
    "12-31-2024",  # Ambiguous M-D-Y
    "13-01-2024",  # D-M-Y with day > 12 (unambiguous)
    "01-13-2024",  # M-D-Y with month > 12 (impossible)
]

for test_str in ymd_test_strings:
    match = extractors.YMD_PATTERN.search(test_str)
    if match:
        groups = match.groupdict()
        print(f"'{test_str}' matched: {groups}")
        # Try to parse
        result = extractors.custom_parse(
            test_str, 
            "%Y-%m-%d", 
            datetime(2020, 1, 1), 
            datetime(2030, 12, 31)
        )
        print(f"  -> custom_parse result: {result}")
    else:
        print(f"'{test_str}' - no match")

print("\n" + "="*60)
print("Testing try_date_expr with edge cases...")
print("="*60)

edge_strings = [
    "2024-02-30",  # Invalid Feb 30
    "2024-04-31",  # Invalid April 31
    "2024-06-31",  # Invalid June 31
    "2024-09-31",  # Invalid Sept 31
    "2024-11-31",  # Invalid Nov 31
    "2024-13-01",  # Invalid month
    "2024-00-15",  # Month = 0
    "2024-12-00",  # Day = 0
    "2024-12-32",  # Day > 31
    "32/12/2024",  # Day > 31 in different format
    "00/01/2024",  # Day = 0 in different format
]

for test_str in edge_strings:
    result = extractors.try_date_expr(
        test_str,
        "%Y-%m-%d",
        False,  # extensive_search
        datetime(2020, 1, 1),
        datetime(2030, 12, 31)
    )
    print(f"try_date_expr('{test_str}') = {result}")

print("\n" + "="*60)
print("Testing regex_parse with ambiguous dates...")
print("="*60)

# Test ambiguous date strings with regex_parse
ambiguous_cases = [
    "March 32, 2024",     # Invalid day > 31
    "February 30, 2024",  # Invalid day for February
    "April 31st, 2024",   # Invalid day for April
    "June 31, 2024",      # Invalid day for June
    "31st of June 2024",  # Different format, still invalid
    "September 31, 2024", # Invalid day for September
    "November 31st, 2024", # Invalid day for November
    "0th of January, 2024", # Day = 0
    "January 0, 2024",    # Day = 0 in different format
]

for test_str in ambiguous_cases:
    result = extractors.regex_parse(test_str)
    print(f"regex_parse('{test_str}') = {result}")

print("\n" + "="*60)
print("Testing year correction boundary...")
print("="*60)

# Test the boundary between 1900s and 2000s
boundary_years = [87, 88, 89, 90, 91, 92]
for year in boundary_years:
    corrected = extractors.correct_year(year)
    print(f"correct_year({year:2d}) = {corrected}")

# Test with dates that cross the boundary
print("\nTesting dates with 2-digit years around boundary:")
dates_2digit = [
    "01-01-89",  # Should be 2089
    "01-01-90",  # Should be 1990
    "31-12-89",  # Should be 2089
    "31-12-90",  # Should be 1990
]

for date_str in dates_2digit:
    result = extractors.custom_parse(
        date_str,
        "%Y-%m-%d",
        datetime(1980, 1, 1),
        datetime(2100, 12, 31)
    )
    print(f"custom_parse('{date_str}') = {result}")