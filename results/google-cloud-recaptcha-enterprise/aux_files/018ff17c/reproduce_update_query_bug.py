#!/usr/bin/env python3
"""Minimal reproduction of the update_query idempotence bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.auth import _helpers

# Minimal failing example from Hypothesis
url = 'http://example.com'
params = {'00': '', '0': '0'}

print(f"Original URL: {url}")
print(f"Params to update: {params}")

# Apply update once
updated_once = _helpers.update_query(url, params)
print(f"\nAfter first update: {updated_once}")

# Apply update again with same params - should be idempotent
updated_twice = _helpers.update_query(updated_once, params)
print(f"After second update: {updated_twice}")

# Check if idempotent
if updated_once == updated_twice:
    print("\n✓ update_query is idempotent")
else:
    print(f"\n✗ BUG: update_query is NOT idempotent!")
    print(f"  First:  {updated_once}")
    print(f"  Second: {updated_twice}")
    
# The issue is the query parameter order changes