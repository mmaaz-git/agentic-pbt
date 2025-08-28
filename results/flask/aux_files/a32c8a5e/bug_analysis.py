#!/usr/bin/env python3
"""Comprehensive analysis of bugs found in troposphere.bedrock validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import positive_integer, integer_range

print("=" * 60)
print("BUG ANALYSIS REPORT: troposphere.validators")
print("=" * 60)

# Bug 1: positive_integer accepts 0
print("\n[BUG 1] positive_integer accepts zero")
print("-" * 40)
print("Testing positive_integer(0):")
try:
    result = positive_integer(0)
    print(f"Result: {result}")
    print("✗ BUG CONFIRMED: Zero was accepted as a positive integer!")
    print("  Mathematical definition: positive integers are > 0, not >= 0")
    print("  Impact: May cause logic errors in AWS configurations")
    bug1_found = True
except ValueError as e:
    print(f"Correctly rejected: {e}")
    bug1_found = False

# Bug 2: integer_range error message formatting
print("\n[BUG 2] integer_range error message uses wrong format specifier")
print("-" * 40)
print("Creating integer_range(1.5, 10.5) and testing with value 0:")
validator = integer_range(1.5, 10.5)
try:
    result = validator(0)
    print(f"Unexpectedly accepted: {result}")
    bug2_found = False
except ValueError as e:
    error_msg = str(e)
    print(f"Error message: {error_msg}")
    if "between 1 and 10" in error_msg:
        print("✗ BUG CONFIRMED: Float bounds truncated to integers in error!")
        print("  Expected: 'Integer must be between 1.5 and 10.5'")
        print(f"  Actual: '{error_msg}'")
        print("  Impact: Misleading error messages for users")
        bug2_found = True
    else:
        print("Bug not confirmed in this test")
        bug2_found = False

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
bugs_found = []
if bug1_found:
    bugs_found.append("positive_integer accepts 0")
if bug2_found:
    bugs_found.append("integer_range error message truncates float bounds")

if bugs_found:
    print(f"Bugs found: {len(bugs_found)}")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("No bugs confirmed in this analysis")

# Reproduce the bugs with minimal code
print("\n" + "=" * 60)
print("MINIMAL REPRODUCTION")
print("=" * 60)

if bug1_found:
    print("\n# Bug 1: positive_integer accepts zero")
    print("from troposphere.validators import positive_integer")
    print("result = positive_integer(0)  # Should raise ValueError")
    print(f"print(result)  # Prints: {positive_integer(0)}")

if bug2_found:
    print("\n# Bug 2: integer_range error message")
    print("from troposphere.validators import integer_range")
    print("validator = integer_range(1.5, 10.5)")
    print("try:")
    print("    validator(0)")
    print("except ValueError as e:")
    print("    print(e)  # Shows bounds as '1 and 10' instead of '1.5 and 10.5'")