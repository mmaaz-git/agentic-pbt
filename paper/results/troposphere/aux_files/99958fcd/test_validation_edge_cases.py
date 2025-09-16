#!/usr/bin/env python3
"""Test edge cases in troposphere validators."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean, integer, double

print("Testing edge cases in troposphere validators...")
print("=" * 60)

# Test 1: Boolean validator with numeric strings
print("\n1. Boolean validator with string '1' and '0':")
test_cases = [
    ("1", True, "String '1' should return True"),
    ("0", False, "String '0' should return False"),
    (1, True, "Integer 1 should return True"),
    (0, False, "Integer 0 should return False"),
]

for value, expected, description in test_cases:
    try:
        result = boolean(value)
        if result == expected:
            print(f"   ✓ {description} - Got {result}")
        else:
            print(f"   ✗ {description} - Expected {expected}, got {result}")
    except Exception as e:
        print(f"   ✗ {description} - Raised {e}")

# Test 2: Integer validator with floats that are whole numbers
print("\n2. Integer validator with float-like values:")
test_cases = [
    (1.0, "Float 1.0 (whole number)"),
    (42.0, "Float 42.0 (whole number)"),
    (3.14, "Float 3.14 (decimal)"),
    ("42", "String '42'"),
    ("-10", "String '-10'"),
]

for value, description in test_cases:
    try:
        result = integer(value)
        print(f"   ✓ {description} accepted: {result}")
    except ValueError as e:
        print(f"   ✗ {description} rejected: {e}")

# Test 3: Double validator with various numeric formats
print("\n3. Double validator with different numeric formats:")
test_cases = [
    ("3.14", "String '3.14'"),
    ("1e5", "Scientific notation '1e5'"),
    ("1.5e-3", "Scientific notation '1.5e-3'"),
    ("-42.0", "Negative float string"),
    ("inf", "String 'inf'"),
    ("nan", "String 'nan'"),
]

for value, description in test_cases:
    try:
        result = double(value)
        print(f"   ✓ {description} accepted: {result}")
    except ValueError as e:
        print(f"   ✗ {description} rejected: {e}")

# Test 4: Check if validators preserve input type
print("\n4. Checking if validators preserve input type:")
test_cases = [
    (integer, 42, "integer(42)"),
    (integer, "42", "integer('42')"),
    (double, 3.14, "double(3.14)"),
    (double, "3.14", "double('3.14')"),
]

for validator, value, description in test_cases:
    try:
        result = validator(value)
        if result is value:
            print(f"   ✓ {description} preserves input: {result} (type: {type(result).__name__})")
        else:
            print(f"   ✗ {description} modifies input: {value} -> {result}")
    except Exception as e:
        print(f"   ✗ {description} failed: {e}")

print("\n" + "=" * 60)
print("Edge case analysis complete!")