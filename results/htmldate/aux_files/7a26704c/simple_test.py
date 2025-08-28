#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate import validators
from htmldate.settings import MIN_DATE

# Test 1: convert_date round-trip
print("Test 1: convert_date round-trip property")
test_date = "2024-01-15"
result = validators.convert_date(test_date, "%Y-%m-%d", "%Y-%m-%d")
print(f"  Input: {test_date}, Output: {result}")
assert result == test_date, f"Round-trip failed: {test_date} != {result}"
print("  ✓ Passed")

# Test 2: Edge case with datetime object input
print("\nTest 2: convert_date with datetime object")
date_obj = datetime(2024, 1, 15)
result = validators.convert_date(date_obj, "%Y-%m-%d", "%Y-%m-%d")
expected = "2024-01-15"
print(f"  Input: datetime object, Output: {result}, Expected: {expected}")
assert result == expected, f"DateTime conversion failed: {result} != {expected}"
print("  ✓ Passed")

# Test 3: is_valid_format with % missing
print("\nTest 3: is_valid_format rejects format without %")
invalid_format = "YYYY-MM-DD"
result = validators.is_valid_format(invalid_format)
print(f"  Format: {invalid_format}, Result: {result}")
assert result == False, f"Invalid format was accepted: {invalid_format}"
print("  ✓ Passed")

# Test 4: is_valid_date boundary check
print("\nTest 4: is_valid_date respects boundaries")
test_date = "2020-06-15"
earliest = datetime(2020, 1, 1)
latest = datetime(2020, 12, 31)
result = validators.is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
print(f"  Date: {test_date}, Within bounds: {result}")
assert result == True, f"Date should be valid within bounds"

# Outside bounds
earliest_outside = datetime(2021, 1, 1)
result_outside = validators.is_valid_date(test_date, "%Y-%m-%d", earliest_outside, latest)
print(f"  Date: {test_date}, Outside bounds: {result_outside}")
assert result_outside == False, f"Date should be invalid outside bounds"
print("  ✓ Passed")

# Test 5: check_date_input with ISO format
print("\nTest 5: check_date_input ISO format parsing")
iso_string = "2024-01-15T10:30:45"
default = datetime(2000, 1, 1)
result = validators.check_date_input(iso_string, default)
print(f"  ISO string: {iso_string}")
print(f"  Result: {result}")
assert result.year == 2024 and result.month == 1 and result.day == 15
print("  ✓ Passed")

# Test 6: check_date_input with invalid input
print("\nTest 6: check_date_input returns default for invalid")
invalid_input = "not-a-date"
result = validators.check_date_input(invalid_input, default)
print(f"  Invalid input: {invalid_input}")
print(f"  Result: {result}, Default: {default}")
assert result == default, f"Should return default for invalid input"
print("  ✓ Passed")

# Test 7: get_min_date with None
print("\nTest 7: get_min_date returns MIN_DATE for None")
result = validators.get_min_date(None)
print(f"  Input: None, Result: {result}, MIN_DATE: {MIN_DATE}")
assert result == MIN_DATE, f"Should return MIN_DATE for None input"
print("  ✓ Passed")

# Test 8: get_max_date with None
print("\nTest 8: get_max_date returns current time for None")
before = datetime.now()
result = validators.get_max_date(None)
after = datetime.now()
print(f"  Input: None, Result: {result}")
print(f"  Within range: {before} <= {result} <= {after}")
assert before <= result <= after
print("  ✓ Passed")

print("\n" + "="*60)
print("All tests passed! ✓")