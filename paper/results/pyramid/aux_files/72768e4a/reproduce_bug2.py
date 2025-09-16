#!/usr/bin/env python3
"""Minimal reproduction for empty package name bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.asset as asset

# Bug 2: Empty package name in spec causes crash
print("Testing spec with empty package name ':'...")
pname, filename = asset.resolve_asset_spec(':', '__main__')
print(f"Resolved to pname='{pname}', filename='{filename}'")

print("\nTrying to get abspath with empty package name...")
try:
    result = asset.abspath_from_asset_spec(':', '__main__')
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError: {e}")
    print("This crashes because it tries to import an empty module name")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError: {e}")

print("\n\nTesting spec with non-existent package '0:'...")
pname, filename = asset.resolve_asset_spec('0:', '__main__')
print(f"Resolved to pname='{pname}', filename='{filename}'")

print("\nTrying to get abspath with non-existent package...")
try:
    result = asset.abspath_from_asset_spec('0:', '__main__')
    print(f"Result: {result}")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError: {e}")
    print("This crashes trying to import module '0'")