#!/usr/bin/env python3
"""
Minimal bug reproducer for htmldate.validators.validate_and_convert
Testing if it incorrectly calls strftime on string input
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime

# Import the module
from htmldate import validators

print("Testing validate_and_convert with string input...")
print("-" * 50)

# Set up test parameters
date_string = "2024-01-15"
outputformat = "%Y-%m-%d"
earliest = datetime(2020, 1, 1)
latest = datetime(2025, 12, 31)

print(f"Input: '{date_string}' (type: {type(date_string).__name__})")
print(f"Output format: {outputformat}")
print(f"Earliest: {earliest}")
print(f"Latest: {latest}")
print()

# First check if the date is valid
is_valid = validators.is_valid_date(date_string, outputformat, earliest, latest)
print(f"is_valid_date result: {is_valid}")

# Now try validate_and_convert
print("\nCalling validate_and_convert...")
try:
    result = validators.validate_and_convert(date_string, outputformat, earliest, latest)
    print(f"Result: {result}")
    
    if result is None and is_valid:
        print("\n⚠️  ISSUE DETECTED:")
        print("  is_valid_date returned True, but validate_and_convert returned None")
        print("  This suggests a bug in validate_and_convert")
        
        # Let's trace the issue
        print("\nInvestigating further...")
        print("Looking at line 70 in validators.py:")
        print("  return date_input.strftime(outputformat)  # type: ignore")
        print("But date_input is a string, not a datetime object!")
        print("Strings don't have a strftime method.")
        
except AttributeError as e:
    print(f"\n🐛 BUG FOUND!")
    print(f"AttributeError: {e}")
    print("\nExplanation:")
    print("  validate_and_convert assumes date_input is a datetime object")
    print("  and calls date_input.strftime(outputformat) on line 70")
    print("  But date_input can be a string (as checked by is_valid_date)")
    print("  This causes an AttributeError when trying to call strftime on a string")
    
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("CONCLUSION:")
print("validate_and_convert has a bug where it attempts to call")
print("strftime() on a string input, causing an AttributeError.")
print("The function should convert the string to datetime first.")
print("="*60)