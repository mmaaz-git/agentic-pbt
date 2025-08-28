#!/usr/bin/env python3
"""Simple single test to check troposphere.identitystore."""

import sys
import json

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.identitystore import Group, GroupMembership, MemberId

# Test 1: Basic Group creation
print("Test 1: Basic Group creation")
try:
    group = Group(
        title="MyGroup",
        DisplayName="Test Display Name",
        IdentityStoreId="store-123"
    )
    group_dict = group.to_dict()
    print(f"  Group dict: {group_dict}")
    assert group_dict['Type'] == 'AWS::IdentityStore::Group'
    print("  ✓ Passed")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 2: Missing required property
print("\nTest 2: Missing required property validation")
try:
    group = Group(title="MyGroup")
    group_dict = group.to_dict()  # Should raise error
    print("  ✗ Failed: Should have raised ValueError for missing required property")
except ValueError as e:
    if "required" in str(e):
        print(f"  ✓ Passed: {e}")
    else:
        print(f"  ✗ Failed: Wrong error: {e}")
except Exception as e:
    print(f"  ✗ Failed: Unexpected error: {e}")

# Test 3: Invalid title
print("\nTest 3: Invalid title validation")
try:
    group = Group(
        title="My-Group",  # Hyphen is not alphanumeric
        DisplayName="Test",
        IdentityStoreId="store-123"
    )
    print("  ✗ Failed: Should have raised ValueError for invalid title")
except ValueError as e:
    if "alphanumeric" in str(e):
        print(f"  ✓ Passed: {e}")
    else:
        print(f"  ✗ Failed: Wrong error: {e}")
except Exception as e:
    print(f"  ✗ Failed: Unexpected error: {e}")

# Test 4: GroupMembership with MemberId
print("\nTest 4: GroupMembership with nested MemberId")
try:
    member = MemberId(UserId="user-456")
    membership = GroupMembership(
        title="MyMembership",
        GroupId="group-123",
        IdentityStoreId="store-123",
        MemberId=member
    )
    membership_dict = membership.to_dict()
    assert membership_dict['Properties']['MemberId']['UserId'] == "user-456"
    print("  ✓ Passed")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 5: Type validation
print("\nTest 5: Type validation for string properties")
try:
    group = Group(
        title="MyGroup",
        DisplayName=123,  # Should be string
        IdentityStoreId="store-123"
    )
    print("  ✗ Failed: Should have raised TypeError for non-string DisplayName")
except TypeError as e:
    print(f"  ✓ Passed: {e}")
except Exception as e:
    print(f"  ✗ Failed: Unexpected error: {e}")

print("\nAll basic tests completed!")