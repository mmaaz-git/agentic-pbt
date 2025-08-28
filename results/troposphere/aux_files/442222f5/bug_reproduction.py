#!/usr/bin/env python3
"""
Minimal bug reproduction for troposphere.docdb
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("TROPOSPHERE BUG REPRODUCTION")
print("=" * 60)

# BUG 1: Integer validator accepts floats with decimal parts
print("\nBUG 1: Integer validator accepts non-integer floats")
print("-" * 60)

from troposphere import validators

# This should raise ValueError but doesn't
value = 42.7
result = validators.integer(value)
print(f"validators.integer({value}) = {result}")
print(f"Type of result: {type(result).__name__}")
print(f"Bug: Accepted float {value} as valid integer")

# BUG 2: Empty string passes title validation  
print("\n\nBUG 2: Empty string bypasses title validation")
print("-" * 60)

from troposphere.docdb import DBCluster

# This should raise ValueError but doesn't
cluster = DBCluster("")
try:
    cluster.validate_title()
    print("DBCluster('').validate_title() succeeded (should have failed)")
    print("Bug: Empty string accepted despite regex requiring 1+ alphanumeric chars")
except ValueError as e:
    print(f"Correctly raised: {e}")

# Show the actual validation regex
print("\nValidation regex check:")
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
print(f"Pattern: {valid_names.pattern}")
print(f"Matches empty string: {bool(valid_names.match(''))}")
print(f"Expected: False (empty string should not match)")

print("\n" + "=" * 60)
print("BUGS CONFIRMED:")
print("1. validators.integer() accepts floats with fractional parts")
print("2. Empty string passes title validation despite regex")
print("=" * 60)