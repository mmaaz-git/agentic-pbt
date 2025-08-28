#!/usr/bin/env python3
"""Reproduce the bugs found in spnego module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from spnego._context import split_username
from spnego._credential import unify_credentials, Password, CredentialCache

# Bug 1: split_username with backslash as domain
print("Bug 1: split_username with backslash as domain")
print("-" * 50)

# Test case that fails
username = "\\user"
domain, user = split_username(username)
print(f"Input: '{username}'")
print(f"Expected domain: '\\'")
print(f"Actual domain: '{domain}'")
print(f"User: '{user}'")
print()

# This is because in Python: "\\user".split("\\", 1) returns ['', 'user']
print("Python string split behavior:")
print(f'"\\\\user".split("\\\\", 1) = {username.split(chr(92), 1)}')
print()

# Bug 2: unify_credentials not preserving all credentials
print("\nBug 2: unify_credentials not preserving all credentials")
print("-" * 50)

cred1 = Password(username="user1", password="pass1")
cred2 = CredentialCache(username="user2")

print(f"Input credentials:")
print(f"  cred1: {cred1}")
print(f"  cred2: {cred2}")

creds = unify_credentials([cred1, cred2])
print(f"\nOutput credentials count: {len(creds)}")
print(f"Output credentials: {creds}")

# Let's investigate why
print("\nInvestigating credential protocols...")
print(f"cred1.supported_protocols: {cred1.supported_protocols}")
print(f"cred2.supported_protocols: {cred2.supported_protocols}")

# Try with different order
print("\nTrying with different order...")
creds_reversed = unify_credentials([cred2, cred1])
print(f"Reversed order count: {len(creds_reversed)}")
print(f"Reversed order: {creds_reversed}")