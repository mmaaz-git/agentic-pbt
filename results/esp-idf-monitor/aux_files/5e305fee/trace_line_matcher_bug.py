#!/usr/bin/env python3
"""Trace through the LineMatcher bug step by step"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

# Manually trace through what LineMatcher does
print("=== Tracing LineMatcher initialization ===\n")

# The problematic input
tag_with_space = ' 0'
level = 'E'
filter_str = f"{tag_with_space}:{level}"

print(f"Initial filter string: '{filter_str}'")

# Step 1: split() on whitespace
items = filter_str.split()
print(f"After split(): {items}")

# Step 2: For each item, split on ':'
for f in items:
    s = f.split(':')
    print(f"Splitting '{f}' on ':' gives: {s}")
    tag_stored = s[0]
    level_stored = s[1] if len(s) > 1 else 'V'
    print(f"Tag stored in dict: '{tag_stored}'")
    print(f"Level stored: '{level_stored}'")

print("\n=== What happens during matching ===\n")

# During matching, the regex extracts the tag from the line
test_line = f"E (12345) {tag_with_space}: Test message"
print(f"Test line: '{test_line}'")

import re
pattern = re.compile(
    r'^(?:\033\[[01];?\d+m?)?'  # ANSI color
    r'([EWIDV]) '  # log level
    r'(?:\([^)]+\) )?'  # optional timestamp
    r'([^:]+): '  # tag
)

match = pattern.search(test_line)
if match:
    extracted_tag = match.group(2)
    print(f"Tag extracted by regex: '{extracted_tag}'")
    print(f"Tag stored in dict: '{tag_stored}'")
    print(f"Do they match? {extracted_tag == tag_stored}")
    print(f"This explains why the match fails!")

print("\n=== The Root Cause ===")
print("The filter parsing uses split() which strips whitespace,")
print("but the regex during matching preserves the exact tag with spaces.")
print("This creates an inconsistency when tags have leading/trailing spaces.")