#!/usr/bin/env python3
"""Minimal reproduction of the scopes round-trip bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.auth import _helpers

# Test case 1: List with empty strings
scopes1 = ['', '']
print(f"Original scopes: {scopes1}")

as_string1 = _helpers.scopes_to_string(scopes1)
print(f"As string: {repr(as_string1)}")

back_to_list1 = _helpers.string_to_scopes(as_string1)
print(f"Back to list: {back_to_list1}")
print(f"Round-trip successful? {scopes1 == back_to_list1}\n")

# Test case 2: Empty list
scopes2 = []
print(f"Original scopes: {scopes2}")

as_string2 = _helpers.scopes_to_string(scopes2)
print(f"As string: {repr(as_string2)}")

back_to_list2 = _helpers.string_to_scopes(as_string2)
print(f"Back to list: {back_to_list2}")
print(f"Round-trip successful? {scopes2 == back_to_list2}\n")

# Test case 3: Mix of empty and non-empty
scopes3 = ['scope1', '', 'scope2']
print(f"Original scopes: {scopes3}")

as_string3 = _helpers.scopes_to_string(scopes3)
print(f"As string: {repr(as_string3)}")

back_to_list3 = _helpers.string_to_scopes(as_string3)
print(f"Back to list: {back_to_list3}")
print(f"Round-trip successful? {scopes3 == back_to_list3}")