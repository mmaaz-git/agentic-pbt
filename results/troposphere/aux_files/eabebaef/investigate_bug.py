#!/usr/bin/env python3
"""Investigate the bug with MaximumMatchDistance accepting floats"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import macie
from troposphere.validators import integer

# Test 1: Reproduce the bug with minimal example
print("Test 1: Creating CustomDataIdentifier with float value for MaximumMatchDistance")
try:
    cdi = macie.CustomDataIdentifier(
        title="TestCDI",
        Name="TestName",
        Regex=".*",
        MaximumMatchDistance=1.1  # This is a float, should it be accepted?
    )
    print(f"✓ Object created successfully")
    print(f"  MaximumMatchDistance value: {cdi.MaximumMatchDistance}")
    print(f"  Type: {type(cdi.MaximumMatchDistance)}")
    
    # Check if it serializes correctly
    result = cdi.to_dict()
    print(f"  Serialized value: {result['Properties']['MaximumMatchDistance']}")
    print(f"  Serialized type: {type(result['Properties']['MaximumMatchDistance'])}")
    
except Exception as e:
    print(f"✗ Failed with error: {e}")

print("\n" + "-" * 60)

# Test 2: Check what the integer validator does
print("Test 2: Checking the integer validator function")
print(f"integer validator function: {integer}")

# Test various values with the integer validator
test_values = [1, 1.0, 1.1, "1", None, True, False]
for val in test_values:
    try:
        result = integer(val)
        print(f"  integer({val!r}) = {result!r} (type: {type(result).__name__})")
    except Exception as e:
        print(f"  integer({val!r}) raised: {e}")

print("\n" + "-" * 60)

# Test 3: Check the props definition for CustomDataIdentifier
print("Test 3: Checking CustomDataIdentifier.props definition")
print(f"MaximumMatchDistance prop definition: {macie.CustomDataIdentifier.props.get('MaximumMatchDistance')}")

print("\n" + "-" * 60)

# Test 4: Test edge cases
print("Test 4: Testing edge cases")
edge_cases = [1.0, 2.0, 3.0, -1.5, 0.0, float('inf')]
for val in edge_cases:
    try:
        cdi = macie.CustomDataIdentifier(
            title="TestCDI",
            Name="TestName",
            Regex=".*",
            MaximumMatchDistance=val
        )
        serialized = cdi.to_dict()['Properties']['MaximumMatchDistance']
        print(f"  {val:10} → accepted, serialized as {serialized} (type: {type(serialized).__name__})")
    except Exception as e:
        print(f"  {val:10} → rejected: {e}")