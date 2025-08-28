#!/usr/bin/env python3
"""Minimal reproduction of the empty title bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import cognito

# Test 1: Empty string title
print("Test 1: Empty string title")
try:
    pool = cognito.IdentityPool(
        title="",
        AllowUnauthenticatedIdentities=True
    )
    print(f"  Created pool with empty title: pool.title = '{pool.title}'")
except ValueError as e:
    print(f"  Raised ValueError: {e}")

# Test 2: None title
print("\nTest 2: None title")
try:
    pool = cognito.IdentityPool(
        title=None,
        AllowUnauthenticatedIdentities=True
    )
    print(f"  Created pool with None title: pool.title = {pool.title}")
except ValueError as e:
    print(f"  Raised ValueError: {e}")

# Test 3: Valid title
print("\nTest 3: Valid alphanumeric title")
try:
    pool = cognito.IdentityPool(
        title="TestPool123",
        AllowUnauthenticatedIdentities=True
    )
    print(f"  Created pool with valid title: pool.title = '{pool.title}'")
except ValueError as e:
    print(f"  Raised ValueError: {e}")

# Test 4: Invalid title with dash
print("\nTest 4: Invalid title with dash")
try:
    pool = cognito.IdentityPool(
        title="test-pool",
        AllowUnauthenticatedIdentities=True
    )
    print(f"  Created pool with dash in title: pool.title = '{pool.title}'")
except ValueError as e:
    print(f"  Raised ValueError: {e}")

# Let's look at the validate_title implementation more closely
print("\n\nChecking validate_title logic:")
from troposphere import valid_names
print(f"valid_names pattern: {valid_names.pattern}")
print(f"Empty string matches pattern: {bool(valid_names.match(''))}")
print(f"None matches pattern: {bool(valid_names.match(None) if None else False)}")
print(f"'TestPool' matches pattern: {bool(valid_names.match('TestPool'))}")
print(f"'test-pool' matches pattern: {bool(valid_names.match('test-pool'))}")