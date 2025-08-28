#!/usr/bin/env python3
"""Verify the title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import cognito

# Create pool with empty title
print("Creating IdentityPool with empty title...")
pool = cognito.IdentityPool(
    title="",
    AllowUnauthenticatedIdentities=True
)
print(f"Success! pool.title = '{pool.title}'")

# Now try to call validate_title directly
print("\nCalling validate_title() directly on the pool with empty title...")
try:
    pool.validate_title()
    print("validate_title() passed (unexpected!)")
except ValueError as e:
    print(f"validate_title() raised ValueError: {e}")

# Create pool with None title
print("\n\nCreating IdentityPool with None title...")
pool2 = cognito.IdentityPool(
    title=None,
    AllowUnauthenticatedIdentities=True
)
print(f"Success! pool2.title = {pool2.title}")

# Try validate_title on None
print("\nCalling validate_title() directly on the pool with None title...")
try:
    pool2.validate_title()
    print("validate_title() passed (unexpected!)")
except ValueError as e:
    print(f"validate_title() raised ValueError: {e}")

# Now test what happens when we call to_dict()
print("\n\nTesting to_dict() behavior:")
print("Calling to_dict() on pool with empty title...")
try:
    result = pool.to_dict()
    print(f"to_dict() succeeded! Result: {result}")
except Exception as e:
    print(f"to_dict() failed: {e}")

print("\nCalling to_dict() on pool with None title...")
try:
    result2 = pool2.to_dict()
    print(f"to_dict() succeeded! Result: {result2}")
except Exception as e:
    print(f"to_dict() failed: {e}")