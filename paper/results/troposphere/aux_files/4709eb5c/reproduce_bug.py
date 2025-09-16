#!/usr/bin/env python3
"""Minimal reproduction of the alphanumeric validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.datasync as datasync

# Test various characters
test_chars = [
    'µ',  # Greek letter mu - Python considers this alphanumeric
    'α',  # Greek letter alpha
    'β',  # Greek letter beta
    '①',  # Circled digit one
    'Ⅻ',  # Roman numeral twelve
    '𝟏',  # Mathematical bold digit one
]

print("Testing title validation with Unicode alphanumeric characters:")
print("-" * 60)

for char in test_chars:
    title = f"Test{char}Name"
    print(f"\nTesting title: '{title}'")
    print(f"  Python isalnum(): {title.isalnum()}")
    
    try:
        agent = datasync.Agent(title=title)
        print(f"  ✓ Title accepted by troposphere")
    except ValueError as e:
        print(f"  ✗ Title rejected: {e}")

# Also test the regex pattern directly
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("\n" + "-" * 60)
print("Direct regex pattern test:")
for char in test_chars:
    title = f"Test{char}Name"
    matches = bool(valid_names.match(title))
    print(f"  '{title}' matches regex: {matches}, Python isalnum(): {title.isalnum()}")