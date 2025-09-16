#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import json

print("=== Understanding the integer validator behavior ===\n")

# Check what the validator actually does
print("Integer validator source:")
import inspect
print(inspect.getsource(integer))

print("\n=== Testing the actual conversion ===")

test_cases = [
    "7",       # ASCII digit
    "๗",       # Thai digit
    "੭",       # Gurmukhi digit
    "೭",       # Kannada digit
]

for test in test_cases:
    print(f"\nTesting '{test}':")
    print(f"  repr: {repr(test)}")
    print(f"  ord: {ord(test)}")
    
    # Test int() conversion
    try:
        int_val = int(test)
        print(f"  int('{test}') = {int_val}")
    except ValueError as e:
        print(f"  int('{test}') raised: {e}")
    
    # Test validator
    try:
        result = integer(test)
        print(f"  integer('{test}') = {repr(result)}")
    except ValueError as e:
        print(f"  integer('{test}') raised: {e}")
    
    # Test JSON serialization
    data = {"value": test}
    json_str = json.dumps(data)
    print(f"  JSON: {json_str}")
    parsed = json.loads(json_str)
    print(f"  Parsed back: {parsed['value']}")

print("\n=== The actual problem ===")
print("The integer validator accepts Unicode digits, which Python's int() can parse.")
print("However, when these are serialized to CloudFormation templates:")
print("1. The Unicode characters are preserved as strings")
print("2. CloudFormation may not handle Unicode digits correctly")
print("3. This creates a mismatch between what troposphere accepts and what AWS expects")

# Show CloudFormation template generation
import troposphere.kendra as kendra
from troposphere import Template

template = Template()
config = kendra.CapacityUnitsConfiguration(
    QueryCapacityUnits="๗",  # Thai 7
    StorageCapacityUnits=7    # Regular 7
)

print("\n=== CloudFormation template output ===")
# Simulate what would be in the template
print(f"Properties that would be in CloudFormation:")
print(json.dumps(config.to_dict(), indent=2))

print("\nThis shows the bug: Unicode digits are accepted but produce")
print("CloudFormation templates that may not work correctly with AWS.")