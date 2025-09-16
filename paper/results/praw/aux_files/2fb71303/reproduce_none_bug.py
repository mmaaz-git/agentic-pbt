#!/usr/bin/env python3
"""Reproduce the None handling bug in permissions_string."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from praw.models.util import permissions_string

print("Bug Reproduction: permissions_string treats None as string 'None'")
print("=" * 70)

# Test case 1: None in the permissions list
known_permissions = {"read", "write", "execute"}
permissions_with_none = ["read", None, "write"]

print("\nTest 1: List containing None")
print(f"Known permissions: {known_permissions}")
print(f"Given permissions: {permissions_with_none}")

result = permissions_string(known_permissions=known_permissions, permissions=permissions_with_none)
print(f"Result: {result}")
print(f"Bug: '+None' appears in result: {'+None' in result}")

# Test case 2: List with only None
print("\nTest 2: List with only [None]")
permissions_only_none = [None]
print(f"Known permissions: {known_permissions}")
print(f"Given permissions: {permissions_only_none}")

result2 = permissions_string(known_permissions=known_permissions, permissions=permissions_only_none)
print(f"Result: {result2}")
print(f"Bug: '+None' appears in result: {'+None' in result2}")

# Test case 3: Multiple None values
print("\nTest 3: Multiple None values")
permissions_multiple_none = [None, "read", None, None]
print(f"Known permissions: {known_permissions}")
print(f"Given permissions: {permissions_multiple_none}")

result3 = permissions_string(known_permissions=known_permissions, permissions=permissions_multiple_none)
print(f"Result: {result3}")
print(f"Bug: '+None' appears multiple times: {result3.count('+None')}")

print("\n" + "=" * 70)
print("ANALYSIS:")
print("The function doesn't validate that permission values are strings.")
print("When None is in the list, it gets converted to the string 'None'")
print("and treated as a valid permission name, which is incorrect.")
print("\nExpected behavior: Should either:")
print("1. Raise a TypeError when None is in the permissions list")
print("2. Filter out None values before processing")
print("3. Document that None values will be stringified")