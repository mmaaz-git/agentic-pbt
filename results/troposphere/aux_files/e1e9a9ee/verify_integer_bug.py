#!/usr/bin/env python3
"""Verify the integer validator bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import licensemanager
from troposphere import validators
import json

print("=== VERIFYING INTEGER VALIDATOR BUG ===\n")

# Test 1: Direct validator test
print("1. Testing integer validator directly:")
test_value = "123"
result = validators.integer(test_value)
print(f"   Input: {test_value!r} (type: {type(test_value).__name__})")
print(f"   Output: {result!r} (type: {type(result).__name__})")
print(f"   Bug confirmed: Returns string instead of integer!\n")

# Test 2: Test in actual usage with BorrowConfiguration
print("2. Testing in BorrowConfiguration:")
config = licensemanager.BorrowConfiguration(
    AllowEarlyCheckIn=True,
    MaxTimeToLiveInMinutes="60"  # Pass string instead of int
)

# Convert to dict to see what gets stored
config_dict = config.to_dict()
print(f"   Input MaxTimeToLiveInMinutes: '60' (string)")
print(f"   Stored value: {config_dict['MaxTimeToLiveInMinutes']!r}")
print(f"   Type: {type(config_dict['MaxTimeToLiveInMinutes']).__name__}")

# Test 3: Check JSON serialization difference
print("\n3. Testing JSON serialization impact:")
config_with_string = licensemanager.BorrowConfiguration(
    AllowEarlyCheckIn=True,
    MaxTimeToLiveInMinutes="60"
)
config_with_int = licensemanager.BorrowConfiguration(
    AllowEarlyCheckIn=True,
    MaxTimeToLiveInMinutes=60
)

json_string = json.dumps(config_with_string.to_dict(), sort_keys=True)
json_int = json.dumps(config_with_int.to_dict(), sort_keys=True)

print(f"   With string '60': {json_string}")
print(f"   With int 60: {json_int}")

if json_string != json_int:
    print("   Bug impact: JSON outputs are different!")
else:
    print("   Note: JSON serialization happens to be the same")

# Test 4: Test with Entitlement MaxCount
print("\n4. Testing with Entitlement MaxCount:")
entitlement = licensemanager.Entitlement(
    Name="TestEntitlement",
    Unit="Count",
    MaxCount="100"
)
ent_dict = entitlement.to_dict()
print(f"   Input MaxCount: '100' (string)")
print(f"   Stored value: {ent_dict['MaxCount']!r}")
print(f"   Type: {type(ent_dict['MaxCount']).__name__}")

print("\n=== BUG VERIFICATION COMPLETE ===")
print("\nSUMMARY: The integer validator accepts strings that look like integers")
print("but returns them as strings instead of converting to actual integers.")
print("This violates the principle of least surprise for a validator named 'integer'.")