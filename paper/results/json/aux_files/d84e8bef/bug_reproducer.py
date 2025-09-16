#!/usr/bin/env python3
"""Minimal bug reproducer for requests.status_codes LookupDict inconsistency."""

import requests.status_codes as sc

# The bug: dict methods are accessible via attribute but not via __getitem__
print("Demonstrating the bug:")
print("======================")

# Method 'items' exists as an attribute (inherited from dict)
print("hasattr(codes, 'items'):", hasattr(sc.codes, 'items'))
print("codes.items:", sc.codes.items)
print("callable(codes.items):", callable(sc.codes.items))

# But accessing via __getitem__ returns None instead
print("codes['items']:", sc.codes['items'])

# This breaks the expected dict-like behavior
print("\nExpected behavior: obj.attr == obj['attr'] for dict-like objects")
print("Actual result: codes.items != codes['items']")
print(f"  codes.items = {sc.codes.items}")
print(f"  codes['items'] = {sc.codes['items']}")

# Practical issue: A user might dynamically access status codes
status_name = "items"  # Could come from user input, config, etc.
code = sc.codes[status_name]
if code is None:
    print(f"\nProblem: User expects a status code for '{status_name}' but gets None")
    print("This silently fails instead of raising KeyError for invalid status names")