"""Reproduction script for is_valid_format bug with empty string"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate.validators import is_valid_format

# Test 1: Empty string should be invalid
format_str = ""
result = is_valid_format(format_str)
print(f"is_valid_format('') = {result}")

if result:
    print("BUG: Empty string marked as valid format")
    # Try to use it
    test_date = datetime(2020, 1, 1)
    try:
        formatted = test_date.strftime(format_str)
        print(f"strftime with empty string produced: '{formatted}'")
    except (ValueError, TypeError) as e:
        print(f"strftime failed as expected: {e}")
else:
    print("Correctly identified empty string as invalid")