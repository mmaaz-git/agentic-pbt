#!/usr/bin/env python3
"""
Confirmed bug reproducer for htmldate.validators.validate_and_convert
The function incorrectly calls strftime on string inputs
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime

# Test the bug
def reproduce_bug():
    from htmldate import validators
    
    # Test case 1: String input (should fail)
    print("Test 1: String input to validate_and_convert")
    date_string = "2024-01-15"
    outputformat = "%Y-%m-%d"
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    
    # First verify the date is valid
    is_valid = validators.is_valid_date(date_string, outputformat, earliest, latest)
    print(f"  is_valid_date('{date_string}', ...) = {is_valid}")
    
    # Now call validate_and_convert
    try:
        result = validators.validate_and_convert(date_string, outputformat, earliest, latest)
        print(f"  validate_and_convert result: {result}")
        return False  # Should have failed
    except AttributeError as e:
        print(f"  ✓ AttributeError as expected: {e}")
        return True
    
def test_with_datetime_object():
    from htmldate import validators
    
    print("\nTest 2: DateTime object input (should work)")
    date_obj = datetime(2024, 1, 15)
    outputformat = "%Y-%m-%d"
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    
    try:
        result = validators.validate_and_convert(date_obj, outputformat, earliest, latest)
        print(f"  validate_and_convert(datetime_obj, ...) = {result}")
        return result == "2024-01-15"
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("BUG REPRODUCTION: validate_and_convert")
    print("="*60)
    
    bug_found = reproduce_bug()
    datetime_works = test_with_datetime_object()
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    if bug_found:
        print("✓ BUG CONFIRMED: validate_and_convert fails with string input")
        print("  The function calls date_input.strftime() on line 70")
        print("  but date_input can be a string (not just datetime)")
        print("  causing AttributeError: 'str' object has no attribute 'strftime'")
        
        print("\nAFFECTED CODE (validators.py, lines 66-73):")
        print("  def validate_and_convert(date_input, outputformat, earliest, latest):")
        print("    if is_valid_date(date_input, outputformat, earliest, latest):")
        print("      try:")
        print("        return date_input.strftime(outputformat)  # BUG: assumes datetime")
        
        print("\nFIX SUGGESTION:")
        print("  Check if date_input is string and convert to datetime first")
        print("  before calling strftime()")
    
    if datetime_works:
        print("\n✓ Function works correctly with datetime objects")
    
    print("="*60)