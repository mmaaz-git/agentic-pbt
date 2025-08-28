#!/usr/bin/env python3
"""Reproduce the title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import analytics

# Test 1: Empty string should fail but doesn't
print("Test 1: Empty string as title")
try:
    app = analytics.Application("")
    print(f"SUCCESS: Created Application with empty title")
    print(f"Title: '{app.title}'")
except ValueError as e:
    print(f"FAILED (as expected): {e}")

# Test 2: Non-alphanumeric should fail
print("\nTest 2: Non-alphanumeric title")
try:
    app = analytics.Application("test-app")
    print(f"SUCCESS: Created Application with title 'test-app'")
except ValueError as e:
    print(f"FAILED (as expected): {e}")

# Test 3: Valid alphanumeric should succeed
print("\nTest 3: Valid alphanumeric title")
try:
    app = analytics.Application("testapp123")
    print(f"SUCCESS: Created Application with title '{app.title}'")
except ValueError as e:
    print(f"FAILED (unexpectedly): {e}")

# Test 4: Check what the validation regex actually is
print("\nTest 4: Checking validation regex")
import re
from troposphere import valid_names

print(f"Regex pattern: {valid_names.pattern}")
print(f"Empty string matches regex: {bool(valid_names.match(''))}")
print(f"Single char 'a' matches regex: {bool(valid_names.match('a'))}")
print(f"'test-app' matches regex: {bool(valid_names.match('test-app'))}")