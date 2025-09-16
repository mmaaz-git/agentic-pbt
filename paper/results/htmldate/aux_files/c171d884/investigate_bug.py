#!/usr/bin/env python3
import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.extractors as extractors
from htmldate.utils import Extractor
from datetime import datetime

# Check the regex pattern used
print("Checking COMPLETE_URL pattern...")
print(f"Pattern: {extractors.COMPLETE_URL.pattern}")

# Test different separators
options = Extractor(
    extensive_search=False,
    max_date=datetime(2040, 12, 31),
    min_date=datetime(1990, 1, 1),
    original_date=False,
    outputformat="%Y-%m-%d"
)

test_urls = [
    ("https://news.com/2021/07/04/story", "slashes"),
    ("https://news.com/2021-07-04-story", "hyphens"),
    ("https://news.com/2021_07_04_story", "underscores"),
    ("https://news.com/2021.07.04.story", "dots"),
    ("https://news.com/article/2021/07/04", "path-end"),
    ("https://news.com/2021/7/4/story", "single-digit"),
]

print("\nTesting URL patterns with different separators:")
for url, desc in test_urls:
    result = extractors.extract_url_date(url, options)
    if result:
        print(f"✅ {desc:15} {url:45} -> {result}")
    else:
        print(f"❌ {desc:15} {url:45} -> None")

# Let's check what the regex actually matches
print("\n\nDirect regex matching test:")
for url, desc in test_urls:
    match = extractors.COMPLETE_URL.search(url)
    if match:
        print(f"Match for {desc}: groups={match.groups()}, full={match[0]}")
    else:
        print(f"No match for {desc}")

# Test edge cases with the regex
print("\n\nTesting edge cases:")
edge_cases = [
    "2021/13/01",  # Invalid month
    "2021/02/30",  # Invalid day for February  
    "2021/00/15",  # Month = 0
    "2021/12/00",  # Day = 0
    "2021/12/32",  # Day > 31
]

for test_string in edge_cases:
    match = extractors.COMPLETE_URL.search(test_string)
    if match:
        print(f"Pattern matched '{test_string}': groups={match.groups()}")
        # Now test if the date validation catches it
        try:
            date = datetime(int(match[1]), int(match[2]), int(match[3]))
            print(f"  -> Created datetime: {date}")
        except ValueError as e:
            print(f"  -> ValueError: {e}")
    else:
        print(f"Pattern didn't match '{test_string}'")

# Check more separator combinations
print("\n\nTesting mixed separators:")
mixed_urls = [
    "https://site.com/2021/07-04-story",     # Mixed / and -
    "https://site.com/2021-07/04-story",     # Mixed - and /
    "https://site.com/2021_07/04_story",     # Mixed _ and /
]

for url in mixed_urls:
    result = extractors.extract_url_date(url, options)
    match = extractors.COMPLETE_URL.search(url)
    print(f"URL: {url}")
    print(f"  Regex match: {match.groups() if match else 'None'}")
    print(f"  Extraction result: {result}")

# Testing regex_parse function with edge cases
print("\n\nTesting regex_parse with various formats:")
test_strings = [
    "January 32, 2024",  # Invalid day
    "February 30, 2024", # Invalid day for February
    "13th of March, 2024", # Month name > 12 doesn't exist
    "December 0, 2024",  # Day = 0
    "June 31, 2024",     # June has only 30 days
]

for test_str in test_strings:
    result = extractors.regex_parse(test_str)
    print(f"regex_parse('{test_str}') = {result}")