#!/usr/bin/env python3
"""Reproduce bug 2: is_valid_format incorrectly validates invalid format codes"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate.validators import is_valid_format

# Test with invalid format codes
invalid_formats = ["%q-%w-%e", "%z%z%z", "%Q", "%W%W%W"]

for fmt in invalid_formats:
    result = is_valid_format(fmt)
    print(f"is_valid_format('{fmt}'): {result}")
    
    # Try to actually use it with strftime to see what happens
    try:
        test_date = datetime(2020, 1, 1)
        formatted = test_date.strftime(fmt)
        print(f"  strftime output: '{formatted}'")
    except (ValueError, KeyError) as e:
        print(f"  strftime error: {e}")
    print()

print("\nBUG: is_valid_format returns True for format strings with invalid codes")