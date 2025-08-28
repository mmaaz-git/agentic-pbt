#!/usr/bin/env python3
"""Test the impact of the negative year bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate.extractors import correct_year

# The bug converts negative years to positive years in the 1900s or 2000s
# This could cause silent data corruption where invalid input produces
# plausible but incorrect dates

test_cases = [
    (-1, "Expected to remain -1 or raise error, but got 1999"),
    (-50, "Expected to remain -50 or raise error, but got 1950"),
    (-99, "Expected to remain -99 or raise error, but got 1901"),
]

print("Testing impact of negative year bug:\n")

for input_year, description in test_cases:
    result = correct_year(input_year)
    print(f"Input: {input_year}")
    print(f"Output: {result}")
    print(f"Issue: {description}")
    
    # Show that this creates valid but wrong dates
    try:
        date = datetime(result, 1, 1)
        print(f"Creates valid date: {date}")
    except ValueError as e:
        print(f"Would fail to create date: {e}")
    print()

print("\nThe function silently converts invalid negative years to valid positive years.")
print("This is a logic bug that causes incorrect date processing.")