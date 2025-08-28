#!/usr/bin/env python3
"""Test the double validator for potential bugs."""

import sys
import math
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import double

print("Testing double validator...")
print("="*50)

# Test various edge cases
test_cases = [
    # (input, should_pass, description)
    (3.14, True, "Normal float"),
    (42, True, "Integer"),
    ("3.14", True, "String float"),
    ("42", True, "String integer"),
    ("-3.14", True, "Negative float string"),
    ("1e10", True, "Scientific notation"),
    ("1E10", True, "Scientific notation uppercase"),
    ("-1.5e-10", True, "Negative scientific"),
    ("inf", True, "Infinity string"),
    ("INF", True, "Uppercase infinity"),
    ("-inf", True, "Negative infinity"),
    ("nan", True, "NaN string"),
    ("NaN", True, "Mixed case NaN"),
    ("NAN", True, "Uppercase NaN"),
    (float('inf'), True, "Infinity float"),
    (float('-inf'), True, "Negative infinity float"),
    (float('nan'), True, "NaN float"),
    ("", False, "Empty string"),
    ("not_a_number", False, "Invalid string"),
    (None, False, "None"),
    ([1, 2, 3], False, "List"),
    ({}, False, "Dict"),
    ("3.14.15", False, "Multiple dots"),
    ("--5", False, "Double negative"),
    ("3e", False, "Incomplete scientific"),
    ("e10", False, "Scientific without mantissa"),
]

print("\nTest results:")
for input_val, should_pass, description in test_cases:
    try:
        result = double(input_val)
        if should_pass:
            print(f"✓ {description:30} double({input_val!r}) = {result}")
        else:
            print(f"✗ {description:30} double({input_val!r}) = {result} (should have raised ValueError)")
    except ValueError as e:
        if not should_pass:
            print(f"✓ {description:30} double({input_val!r}) raised ValueError (expected)")
        else:
            print(f"✗ {description:30} double({input_val!r}) raised ValueError (unexpected)")
    except Exception as e:
        print(f"✗ {description:30} double({input_val!r}) raised {type(e).__name__}: {e}")

print("\n" + "="*50)
print("Checking implementation details...")

# Let's look at what the validator actually does
def double_implementation(x):
    """Reimplementation for analysis"""
    try:
        float(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid double" % x)
    else:
        return x

print("\nThe double validator:")
print("1. Tries to convert input to float")
print("2. If successful, returns the ORIGINAL value (not the converted float)")
print("3. If conversion fails, raises ValueError")

print("\nPotential issue: Returns original value, not converted value")
print("This means:")
result = double("3.14")
print(f"double('3.14') returns: {result!r} (type: {type(result).__name__})")
print(f"Not the float: {float('3.14')} (type: float)")

print("\n" + "="*50)
print("Testing special float values...")

# Test special values
special_tests = [
    (float('inf'), "Positive infinity"),
    (float('-inf'), "Negative infinity"),
    (float('nan'), "NaN"),
    (0.0, "Zero"),
    (-0.0, "Negative zero"),
    (sys.float_info.max, "Max float"),
    (sys.float_info.min, "Min positive float"),
    (-sys.float_info.max, "Min float"),
]

for val, desc in special_tests:
    try:
        result = double(val)
        print(f"✓ {desc:25} double({val}) = {result}")
        # Check if value is preserved exactly
        if math.isnan(val):
            if not math.isnan(result):
                print(f"  ✗ NaN not preserved correctly")
        elif result != val:
            print(f"  ✗ Value not preserved: {result} != {val}")
    except Exception as e:
        print(f"✗ {desc:25} raised {type(e).__name__}: {e}")

print("\n" + "="*50)
print("Edge case: Values that look numeric but aren't...")

edge_cases = [
    "١٢٣",  # Arabic numerals
    "1,234.56",  # Comma separator
    "1 234.56",  # Space separator
    "$123.45",  # Currency symbol
    "123.45%",  # Percentage
    "0x1A",  # Hexadecimal
    "0o17",  # Octal
    "0b1010",  # Binary
    "MCMXCIV",  # Roman numerals
    "3+4j",  # Complex number
    "½",  # Fraction character
    "∞",  # Infinity symbol
    "π",  # Pi symbol
]

for val in edge_cases:
    try:
        result = double(val)
        print(f"✗ Accepted unusual input: double({val!r}) = {result}")
    except ValueError:
        print(f"✓ Rejected: {val!r}")
    except Exception as e:
        print(f"? Unexpected error for {val!r}: {type(e).__name__}")