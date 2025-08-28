#!/usr/bin/env python3
"""
Bug hunting script for htmldate.validators
Looking for edge cases and boundary conditions
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
import traceback

# Import the module
from htmldate import validators
from htmldate.settings import MIN_DATE

print("="*60)
print("BUG HUNTING IN htmldate.validators")
print("="*60)

bugs_found = []

# Test 1: is_valid_format with single % character
print("\n[TEST 1] is_valid_format with single '%' character")
try:
    result = validators.is_valid_format("%")
    print(f"  is_valid_format('%') = {result}")
    # According to the code, it checks if '%' is in the string (line 87)
    # But a single '%' will fail strftime (line 82)
    # So this should return False
    if result == True:
        bugs_found.append("is_valid_format('%') returns True but '%' alone is not a valid format")
except Exception as e:
    print(f"  Exception: {e}")

# Test 2: is_valid_format with '%%' (literal percent)
print("\n[TEST 2] is_valid_format with '%%' (escaped percent)")
try:
    result = validators.is_valid_format("%%")
    print(f"  is_valid_format('%%') = {result}")
    # %% is valid in strftime (represents literal %)
    # But the code checks for '%' in string, so it passes that check
    # strftime should succeed with %%
except Exception as e:
    print(f"  Exception: {e}")

# Test 3: convert_date with datetime input but mismatched inputformat
print("\n[TEST 3] convert_date with datetime object and inputformat")
try:
    date_obj = datetime(2024, 1, 15)
    # Line 176-177 checks isinstance(datestring, datetime) and returns immediately
    # But inputformat is ignored when input is datetime
    result = validators.convert_date(date_obj, "IGNORED_FORMAT", "%Y-%m-%d")
    print(f"  convert_date(datetime_obj, 'IGNORED_FORMAT', '%Y-%m-%d') = {result}")
    print("  Note: inputformat is ignored when datestring is datetime object")
except Exception as e:
    print(f"  Exception: {e}")
    bugs_found.append(f"convert_date with datetime input: {e}")

# Test 4: is_valid_date with edge timestamp comparison
print("\n[TEST 4] is_valid_date timestamp boundary edge case")
try:
    # Create date at midnight
    test_date = "2020-06-15"
    # Earliest at 1 microsecond after midnight on same day
    earliest = datetime(2020, 6, 15, 0, 0, 0, 1)
    latest = datetime(2020, 12, 31)
    
    result = validators.is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
    print(f"  Date: {test_date} (midnight)")
    print(f"  Earliest: {earliest} (00:00:00.000001)")
    print(f"  Result: {result}")
    
    if result == True:
        # The parsed date will be at midnight (00:00:00.000000)
        # which is BEFORE 00:00:00.000001
        # So this should be False but might return True
        bugs_found.append("is_valid_date accepts date at midnight when earliest is after midnight")
except Exception as e:
    print(f"  Exception: {e}")

# Test 5: validate_and_convert attribute error
print("\n[TEST 5] validate_and_convert with string input")
try:
    # Line 70 calls date_input.strftime(outputformat)
    # But date_input might be a string, not datetime
    result = validators.validate_and_convert("2024-01-15", "%Y-%m-%d", 
                                            datetime(2020, 1, 1), datetime(2025, 1, 1))
    print(f"  validate_and_convert('2024-01-15', ...) = {result}")
    if result is None:
        print("  Returned None (might be a bug if date is valid)")
except AttributeError as e:
    print(f"  AttributeError: {e}")
    bugs_found.append(f"validate_and_convert AttributeError: string has no strftime method")
except Exception as e:
    print(f"  Other exception: {e}")

# Test 6: check_date_input with fromisoformat edge cases
print("\n[TEST 6] check_date_input with partial ISO formats")
try:
    # fromisoformat might not handle all ISO variants
    partial_iso = "2024-01-15"  # Date only, no time
    result = validators.check_date_input(partial_iso, datetime(2000, 1, 1))
    print(f"  check_date_input('{partial_iso}') = {result}")
except Exception as e:
    print(f"  Exception: {e}")

# Test 7: plausible_year_filter with None pattern match
print("\n[TEST 7] Looking at plausible_year_filter logic")
# This function is complex but has potential issues:
# Line 106: year_match = yearpat.search(item)
# Line 107-110: if year_match is None, del occurrences[item]
# This modifies dict during iteration which used to cause RuntimeError
# They handle it with list() on line 105, but let's document it
print("  Note: Function uses list(occurrences) to prevent RuntimeError")
print("  when modifying Counter during iteration (line 105)")

# Test 8: compare_values exception handling
print("\n[TEST 8] compare_values with invalid date string")
try:
    from htmldate.utils import Extractor
    options = Extractor(False, datetime(2025,1,1), datetime(2020,1,1), False, "%Y-%m-%d")
    # This should trigger the exception on line 131
    result = validators.compare_values(0, "INVALID_DATE", options)
    print(f"  compare_values with invalid date returns: {result}")
    if result == 0:
        print("  ✓ Returns reference value on exception (as expected)")
except ImportError:
    print("  Could not test - Extractor import issue")
except Exception as e:
    print(f"  Exception: {e}")

# Test 9: Year comparison logic in is_valid_date
print("\n[TEST 9] Year bounds check order in is_valid_date")
try:
    # Line 52-53: checks year first, then timestamp
    # This could lead to edge cases where year passes but timestamp fails
    test_date = "2020-12-31"  # Last day of 2020
    earliest = datetime(2020, 1, 1)
    latest = datetime(2020, 1, 1)  # Same as earliest
    result = validators.is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
    print(f"  Date {test_date} with earliest=latest={earliest}: {result}")
    if result == True:
        bugs_found.append("is_valid_date year check passes but timestamp should fail")
except Exception as e:
    print(f"  Exception: {e}")

# Summary
print("\n" + "="*60)
print("BUG HUNT SUMMARY")
print("="*60)

if bugs_found:
    print(f"\nFound {len(bugs_found)} potential bug(s):")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("\nNo obvious bugs found in basic tests.")
    print("Note: More comprehensive property-based testing might reveal edge cases.")

print("\nRecommendation: Run full Hypothesis test suite for thorough testing.")