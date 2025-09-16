#!/usr/bin/env python3
"""Reproduce bug 1: get_min_date doesn't respect MIN_DATE"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate.settings import MIN_DATE
from htmldate.validators import get_min_date

# MIN_DATE is 1995-01-01
print(f"MIN_DATE: {MIN_DATE}")

# Test with a date before MIN_DATE
test_date = datetime(1994, 1, 1, 0, 0)
print(f"Test date (before MIN_DATE): {test_date}")

result = get_min_date(test_date)
print(f"Result from get_min_date: {result}")

# Expected: Should return MIN_DATE (1995-01-01) since input is before it
# Actual: Returns the input date (1994-01-01)
print(f"\nBUG: get_min_date returned {result} but should return {MIN_DATE} or later")