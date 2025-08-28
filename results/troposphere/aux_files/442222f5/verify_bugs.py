#!/usr/bin/env python3
"""
Standalone bug verification script
"""
import sys
import os

# Add the troposphere path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("Verifying bugs in troposphere.docdb module...")
print("=" * 60)

# Bug 1: Integer validator accepts floats with decimal parts
print("\nBUG 1: Integer validator accepts non-integer floats")
print("-" * 60)

from troposphere import validators

test_float = 42.7
print(f"Testing: validators.integer({test_float})")

try:
    result = validators.integer(test_float)
    print(f"✗ BUG CONFIRMED: Returned {result!r} (type: {type(result).__name__})")
    print(f"  Expected: ValueError to be raised")
    print(f"  Actual: Accepted float {test_float} without error")
    print(f"  Impact: Type validation is incorrect, may cause downstream issues")
    
    # Test with more examples
    print("\n  Additional test cases:")
    for val in [1.1, -5.5, 100.999]:
        try:
            r = validators.integer(val)
            print(f"    integer({val}) = {r!r} ✗ (should reject)")
        except ValueError:
            print(f"    integer({val}) raised ValueError ✓")
            
    bug1_confirmed = True
    
except ValueError as e:
    print(f"✓ No bug: Correctly raised ValueError: {e}")
    bug1_confirmed = False

# Bug 2: Empty string passes title validation
print("\n\nBUG 2: Empty string bypasses title validation")
print("-" * 60)

from troposphere.docdb import DBCluster

print("Testing: DBCluster('').validate_title()")

try:
    cluster = DBCluster("")
    cluster.validate_title()
    print("✗ BUG CONFIRMED: Empty string accepted as valid title")
    print("  Expected: ValueError with 'not alphanumeric' message")
    print("  Actual: No error raised")
    print("  Regex pattern: '^[a-zA-Z0-9]+$' requires 1+ characters")
    print("  Impact: Invalid CloudFormation resource names could be created")
    
    bug2_confirmed = True
    
except ValueError as e:
    print(f"✓ No bug: Correctly raised ValueError: {e}")
    bug2_confirmed = False

# Check the actual regex
print("\n  Investigating regex behavior:")
import re
pattern = re.compile(r'^[a-zA-Z0-9]+$')
print(f"    Pattern: {pattern.pattern}")
print(f"    pattern.match('') = {pattern.match('')}")
print(f"    pattern.match('a') = {pattern.match('a')}")
print(f"    pattern.match('Test123') = {pattern.match('Test123')}")

# Summary
print("\n" + "=" * 60)
print("BUG VERIFICATION SUMMARY")
print("=" * 60)

bugs_found = []
if bug1_confirmed:
    bugs_found.append("1. Integer validator accepts floats with decimal parts")
if bug2_confirmed:
    bugs_found.append("2. Empty string bypasses title validation")

if bugs_found:
    print(f"✗ {len(bugs_found)} BUG(S) CONFIRMED:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ No bugs found")

print("\nNext step: Creating bug reports for confirmed issues..."