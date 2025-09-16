#!/usr/bin/env python3
# Direct import test - testing individual functions without external dependencies
import sys
import os

# Add the htmldate path
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

# Test 1: correct_year function
print("Testing correct_year function...")
import htmldate.extractors as extractors

test_cases = [
    (0, 2000),    # Year 00 -> 2000
    (1, 2001),    # Year 01 -> 2001
    (50, 2050),   # Year 50 -> 2050
    (89, 2089),   # Year 89 -> 2089 (boundary)
    (90, 1990),   # Year 90 -> 1990 (boundary)
    (99, 1999),   # Year 99 -> 1999
    (100, 100),   # Year 100 -> 100 (unchanged)
    (2024, 2024), # Year 2024 -> 2024 (unchanged)
]

for input_year, expected in test_cases:
    result = extractors.correct_year(input_year)
    if result != expected:
        print(f"❌ FAILED: correct_year({input_year}) = {result}, expected {expected}")
    else:
        print(f"✅ correct_year({input_year}) = {result}")

# Test 2: try_swap_values function
print("\nTesting try_swap_values function...")
swap_cases = [
    ((5, 10), (5, 10)),      # Normal case - no swap
    ((5, 13), (13, 5)),      # Month > 12, day <= 12 - should swap
    ((15, 20), (15, 20)),    # Both > 12 - no swap
    ((12, 13), (13, 12)),    # Edge case: day=12, month=13 - should swap
    ((13, 13), (13, 13)),    # Both > 12 - no swap
]

for (day, month), (exp_day, exp_month) in swap_cases:
    result_day, result_month = extractors.try_swap_values(day, month)
    if (result_day, result_month) != (exp_day, exp_month):
        print(f"❌ FAILED: try_swap_values({day}, {month}) = ({result_day}, {result_month}), expected ({exp_day}, {exp_month})")
    else:
        print(f"✅ try_swap_values({day}, {month}) = ({result_day}, {result_month})")

# Test 3: URL date extraction
print("\nTesting extract_url_date function...")
from htmldate.utils import Extractor
from datetime import datetime

options = Extractor(
    extensive_search=False,
    max_date=datetime(2040, 12, 31),
    min_date=datetime(1990, 1, 1),
    original_date=False,
    outputformat="%Y-%m-%d"
)

url_cases = [
    ("https://example.com/2024/01/15/post.html", "2024-01-15"),
    ("https://blog.com/posts/2023/12/25/christmas", "2023-12-25"),
    ("https://site.org/2022-03-10-article", "2022-03-10"),
    ("https://news.com/2021.07.04.story", "2021-07-04"),
]

for url, expected in url_cases:
    result = extractors.extract_url_date(url, options)
    if result != expected:
        print(f"❌ FAILED: extract_url_date('{url}') = {result}, expected {expected}")
    else:
        print(f"✅ extract_url_date('{url}') = {expected}")

# Test 4: Test with invalid dates
print("\nTesting with invalid dates...")
invalid_urls = [
    "https://example.com/2024/13/01/post.html",  # Invalid month
    "https://example.com/2024/02/30/post.html",  # Invalid day for February
    "https://example.com/2024/00/15/post.html",  # Month = 0
]

for url in invalid_urls:
    result = extractors.extract_url_date(url, options)
    if result is not None:
        print(f"⚠️ extract_url_date('{url}') = {result}, expected None for invalid date")
    else:
        print(f"✅ extract_url_date('{url}') correctly returned None for invalid date")

print("\n" + "="*50)
print("Basic tests complete!")