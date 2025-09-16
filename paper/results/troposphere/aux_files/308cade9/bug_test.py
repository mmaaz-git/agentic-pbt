#!/usr/bin/env python3
"""Test for potential bug in validate_backup_selection"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import If
from troposphere.backup import BackupSelectionResourceType

print("Testing potential bug in validate_backup_selection:")
print("=" * 50)

# Create a BackupSelectionResourceType with both ListOfTags and Resources
# as regular values (not If objects)
print("\n1. Testing with both ListOfTags and Resources as regular values:")
selection1 = BackupSelectionResourceType(
    IamRoleArn="arn:aws:iam::123456789012:role/BackupRole",
    SelectionName="TestSelection",
    ListOfTags=[],
    Resources=["arn:aws:ec2:*:*:volume/*"]
)

try:
    selection1.validate()
    print("   ERROR: Validation passed when both were specified!")
except ValueError as e:
    print(f"   OK: Validation failed as expected: {e}")

# Now test with both as If objects (CloudFormation conditionals)
print("\n2. Testing with both ListOfTags and Resources as If objects:")

# Create mock If conditions
condition1 = If("Condition1", [], [])
condition2 = If("Condition2", ["arn:aws:ec2:*:*:volume/*"], [])

selection2 = BackupSelectionResourceType(
    IamRoleArn="arn:aws:iam::123456789012:role/BackupRole",
    SelectionName="TestSelection",
    ListOfTags=condition1,
    Resources=condition2
)

try:
    selection2.validate()
    print("   BUG FOUND: Validation passed when both were If objects!")
    print("   This violates the 'exactly one' requirement!")
except ValueError as e:
    print(f"   OK: Validation failed: {e}")

# Test with only one as If object
print("\n3. Testing with only Resources as If object:")
selection3 = BackupSelectionResourceType(
    IamRoleArn="arn:aws:iam::123456789012:role/BackupRole",
    SelectionName="TestSelection",
    Resources=condition2
)

try:
    selection3.validate()
    print("   OK: Validation passed with one If object")
except ValueError as e:
    print(f"   Unexpected error: {e}")

# Test with neither
print("\n4. Testing with neither ListOfTags nor Resources:")
selection4 = BackupSelectionResourceType(
    IamRoleArn="arn:aws:iam::123456789012:role/BackupRole",
    SelectionName="TestSelection"
)

try:
    selection4.validate()
    print("   ERROR: Validation passed when neither was specified!")
except ValueError as e:
    print(f"   OK: Validation failed as expected: {e}")

print("\n" + "=" * 50)
print("Summary:")
print("The validate_backup_selection function has a logic bug!")
print("When both ListOfTags and Resources are If objects,")
print("the validation is skipped entirely, violating the")
print("'exactly one' constraint that the function is supposed to enforce.")