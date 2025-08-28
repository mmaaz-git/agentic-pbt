#!/usr/bin/env python3
"""Reproduce the bugs found by property-based testing."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Template, Parameter, Tags

print("Bug 1: Tags concatenation loses duplicate keys")
print("=" * 50)

# Create two Tags objects with the same key
tags1 = Tags({'Environment': 'prod'})
tags2 = Tags({'Environment': 'dev'})

# Concatenate them
combined = tags1 + tags2

print(f"tags1.to_dict(): {tags1.to_dict()}")
print(f"tags2.to_dict(): {tags2.to_dict()}")
print(f"combined.to_dict(): {combined.to_dict()}")
print(f"Length of combined: {len(combined.to_dict())}")
print(f"Expected length: {len(tags1.to_dict()) + len(tags2.to_dict())}")

# The bug: when concatenating Tags with duplicate keys, 
# it only keeps one value instead of both
print("\nBUG: Combined tags should have 2 entries but only has 1!")
print("The second 'Environment' tag overwrites the first one.")

print("\n" + "=" * 50)
print("Bug 2: Parameter with Type='Number' accepts empty string")
print("=" * 50)

try:
    # This should fail but doesn't
    param = Parameter("TestParam", Type="Number", Default="")
    param.validate()
    print("BUG: Parameter with Type='Number' accepted empty string '' as default!")
    print(f"Parameter created: {param.properties}")
except ValueError as e:
    print(f"Correctly rejected: {e}")

print("\n" + "=" * 50)
print("Bug 3: Parameter with Type='String' requires string default but claims to accept int")
print("=" * 50)

try:
    # This should work (converting int to string) but fails
    param = Parameter("TestParam2", Type="String", Default=123)
    param.validate()
    print(f"Parameter created with int default: {param.properties}")
except ValueError as e:
    print(f"Error (possible bug): {e}")
    print("NOTE: The error message says it expects String type, but integers")
    print("should be acceptable and converted to strings for String parameters.")

print("\n" + "=" * 50)
print("Bug 4: Character 'ª' is alphanumeric but rejected by valid_names regex")
print("=" * 50)

import re
from troposphere import valid_names

test_char = "ª"
print(f"Is '{test_char}' alphanumeric according to Python? {test_char.isalnum()}")
print(f"Does '{test_char}' match troposphere's valid_names regex? {bool(valid_names.match(test_char))}")
print("BUG: Python's isalnum() and troposphere's regex disagree on what's alphanumeric!")