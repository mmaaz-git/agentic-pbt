#!/usr/bin/env python3
"""Minimal reproduction of the bug in htmldate.extractors.custom_parse"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate.extractors import custom_parse

# Test invalid dates that should return None but instead return first of month
invalid_dates = [
    "2024-02-30",  # February doesn't have 30 days
    "2024-04-31",  # April has only 30 days
    "2024-06-31",  # June has only 30 days
    "2024-12-00",  # Day cannot be 0
]

print("Bug: custom_parse accepts invalid dates and returns first of month\n")

for date_string in invalid_dates:
    result = custom_parse(
        date_string,
        "%Y-%m-%d",
        datetime(2020, 1, 1),
        datetime(2030, 12, 31)
    )
    print(f"custom_parse('{date_string}') = {result}")
    print(f"  Expected: None (invalid date)")
    print(f"  Actual:   {result} (silently converted to first of month)\n")