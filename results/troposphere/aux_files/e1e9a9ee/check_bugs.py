#!/usr/bin/env python3
"""Check for potential bugs in troposphere.licensemanager."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import licensemanager, validators

# Check 1: Test boolean validator edge cases
print("Checking boolean validator edge cases...")

# Check if string "1" and "0" work correctly
test_cases = [
    ("1", True),
    ("0", False),
    (1, True),
    (0, False),
    ("true", True),
    ("false", False),
    ("True", True),
    ("False", False),
    (True, True),
    (False, False)
]

for input_val, expected in test_cases:
    result = validators.boolean(input_val)
    if result != expected:
        print(f"  BUG: boolean({input_val!r}) returned {result}, expected {expected}")
    else:
        print(f"  OK: boolean({input_val!r}) -> {result}")

# Check 2: Test integer validator with edge cases
print("\nChecking integer validator edge cases...")

# The integer validator should accept strings that can be converted to int
int_test_cases = [
    "123",
    "-456",
    "0",
    123,
    -456,
    0,
]

for val in int_test_cases:
    try:
        result = validators.integer(val)
        int_result = int(result)
        print(f"  OK: integer({val!r}) -> {result!r} -> int({int_result})")
    except Exception as e:
        print(f"  ERROR: integer({val!r}) raised {e}")

# Check 3: Test from_dict implementation
print("\nChecking from_dict implementation...")

# Create a Grant object
grant1 = licensemanager.Grant(
    "TestGrant",
    GrantName="MyGrant",
    HomeRegion="us-east-1",
    LicenseArn="arn:aws:license-manager:us-east-1:123456789012:license/abc",
    Principals=["arn:aws:iam::123456789012:role/MyRole"],
    AllowedOperations=["CreateGrant"],
    Status="ACTIVE"
)

# Convert to dict
dict1 = grant1.to_dict()
print(f"  Original dict: {dict1}")

# Try to recreate from dict
props = dict1.get("Properties", {})
grant2 = licensemanager.Grant.from_dict("TestGrant", props)
dict2 = grant2.to_dict()
print(f"  Recreated dict: {dict2}")

if dict1 != dict2:
    print(f"  BUG: Dictionaries don't match after round-trip!")
    print(f"  Difference: {set(dict1.items()) ^ set(dict2.items())}")
else:
    print(f"  OK: Round-trip successful")

# Check 4: Test property validation with type mismatches
print("\nChecking property type validation...")

# BorrowConfiguration expects boolean for AllowEarlyCheckIn
borrow_config = licensemanager.BorrowConfiguration()

# Test with various boolean-like values
boolean_test_values = ["yes", "no", 2, -1, "TRUE", "FALSE"]
for val in boolean_test_values:
    try:
        borrow_config.AllowEarlyCheckIn = val
        # Try to convert to dict to trigger validation
        result = borrow_config.to_dict()
        print(f"  POTENTIAL BUG: AllowEarlyCheckIn accepted {val!r} -> {result.get('AllowEarlyCheckIn')!r}")
    except (ValueError, TypeError) as e:
        print(f"  OK: AllowEarlyCheckIn rejected {val!r}: {e}")

# Check 5: Test empty string as title
print("\nChecking empty string as title...")
try:
    grant = licensemanager.Grant("")
    print(f"  BUG: Empty string accepted as title!")
except ValueError as e:
    print(f"  OK: Empty string rejected: {e}")

# Check 6: Test ValidityDateFormat with missing fields
print("\nChecking ValidityDateFormat with missing fields...")
validity = licensemanager.ValidityDateFormat(Begin="2024-01-01")
try:
    validity.to_dict()
    print(f"  BUG: ValidityDateFormat.to_dict() succeeded without End field!")
except ValueError as e:
    print(f"  OK: Missing End field caught: {e}")

# Check 7: Test equality with None values
print("\nChecking equality with None values...")
grant1 = licensemanager.Grant("Test1")
grant2 = licensemanager.Grant("Test1")

# Both have no properties set
if grant1 == grant2:
    print(f"  OK: Empty grants with same title are equal")
else:
    print(f"  BUG: Empty grants with same title are not equal!")

# Check 8: Test integer validator with float strings
print("\nChecking integer validator with float strings...")
float_strings = ["1.0", "2.5", "3.14", "-1.5"]
for val in float_strings:
    try:
        result = validators.integer(val)
        print(f"  POTENTIAL BUG: integer({val!r}) accepted float string -> {result!r}")
    except ValueError as e:
        print(f"  OK: integer({val!r}) rejected: {e}")

print("\n✅ Bug checking complete!")