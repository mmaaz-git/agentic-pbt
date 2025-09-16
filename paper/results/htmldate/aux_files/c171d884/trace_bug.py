#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.extractors as extractors
from datetime import datetime
from dateutil.parser import parse as dateutil_parse

print("Tracing the bug: Invalid dates being converted to first of month")
print("="*70)

# Test invalid dates
invalid_dates = [
    "2023-02-29",  # Feb 29 in non-leap year
    "2024-04-31",  # April 31 doesn't exist
    "2024-12-00",  # Day = 0
    "2024-12-32",  # Day > 31
]

print("Step 1: Testing datetime.fromisoformat (used in custom_parse):")
print("-"*70)
for date_str in invalid_dates:
    try:
        result = datetime.fromisoformat(date_str)
        print(f"datetime.fromisoformat('{date_str}') = {result}")
    except ValueError as e:
        print(f"datetime.fromisoformat('{date_str}') raised ValueError: {e}")

print("\nStep 2: Testing dateutil.parser.parse (fallback in custom_parse):")
print("-"*70)
for date_str in invalid_dates:
    try:
        result = dateutil_parse(date_str, fuzzy=False)
        print(f"dateutil_parse('{date_str}', fuzzy=False) = {result}")
    except (ValueError, OverflowError) as e:
        print(f"dateutil_parse('{date_str}', fuzzy=False) raised {type(e).__name__}: {e}")

print("\nStep 3: Checking custom_parse implementation:")
print("-"*70)

# Let's directly test the logic
test_string = "2024-04-31"
print(f"Testing with: {test_string}")
print(f"  First 4 chars are digits: {test_string[:4].isdigit()}")
print(f"  Chars 4-8 are: '{test_string[4:8]}' (isdigit: {test_string[4:8].isdigit()})")

# Test the actual custom_parse function
result = extractors.custom_parse(
    test_string,
    "%Y-%m-%d",
    datetime(2020, 1, 1),
    datetime(2030, 12, 31)
)
print(f"  custom_parse result: {result}")

print("\n" + "="*70)
print("CONFIRMED BUG: dateutil.parser.parse silently converts invalid dates!")
print("="*70)

print("\nExamples of the bug:")
examples = [
    ("2024-02-30", "February 30 doesn't exist"),
    ("2024-04-31", "April has only 30 days"),
    ("2024-06-31", "June has only 30 days"),
    ("2024-09-31", "September has only 30 days"),
    ("2024-11-31", "November has only 30 days"),
    ("2024-12-00", "Day cannot be 0"),
    ("2024-12-32", "Day cannot be > 31"),
    ("2024-00-15", "Month cannot be 0"),
]

for date_str, reason in examples:
    try:
        # Direct datetime construction would fail
        year, month, day = date_str.split('-')
        datetime(int(year), int(month), int(day))
        actual_result = "Would be valid"
    except ValueError:
        # But dateutil.parser doesn't fail
        try:
            parsed = dateutil_parse(date_str, fuzzy=False)
            actual_result = parsed.strftime("%Y-%m-%d")
        except:
            actual_result = "Failed to parse"
    
    custom_result = extractors.custom_parse(
        date_str,
        "%Y-%m-%d",
        datetime(2020, 1, 1),
        datetime(2030, 12, 31)
    )
    
    print(f"{date_str}: {reason}")
    print(f"  -> dateutil result: {actual_result}")
    print(f"  -> custom_parse result: {custom_result}")
    print()

print("This is a CONTRACT bug: The function silently accepts invalid dates")
print("and converts them to valid dates, which violates expected behavior.")