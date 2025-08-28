#!/usr/bin/env python3
"""Minimal reproduction for backslash bug in abspath_from_asset_spec"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.asset as asset

# Bug 1: Backslash causes ValueError on Unix systems
print("Testing backslash in spec...")
try:
    result = asset.abspath_from_asset_spec('\\', '__main__')
    print(f"Result: {result}")
except ValueError as e:
    print(f"ERROR: {e}")
    print("This fails even though '\\' is not an absolute path on Unix systems")

print("\nTesting forward slash (control)...")
try:
    result = asset.abspath_from_asset_spec('/', '__main__')
    print(f"Result: {result}")
except Exception as e:
    print(f"ERROR: {e}")

print("\nAnalysis: The function treats backslash as an absolute path marker")
print("even on Unix where it's just a regular character.")