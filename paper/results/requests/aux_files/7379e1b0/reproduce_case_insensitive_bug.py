#!/usr/bin/env python3
"""Minimal reproduction of CaseInsensitiveDict bug with ß character."""

from requests.models import CaseInsensitiveDict

# Create a CaseInsensitiveDict with the German ß character
cid = CaseInsensitiveDict({'ß': 'value'})

# According to the documentation, case-insensitive access should work
print(f"Original key 'ß': {cid.get('ß')}")
print(f"Lowercase 'ß': {cid.get('ß'.lower())}")  
print(f"Uppercase 'SS': {cid.get('ß'.upper())}")

# The bug: 'ß'.upper() returns 'SS', but CaseInsensitiveDict doesn't handle this
assert cid.get('ß') == cid.get('ß'.upper()), f"Expected {cid.get('ß')}, got {cid.get('ß'.upper())}"