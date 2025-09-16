#!/usr/bin/env python3
"""Minimal reproduction of property None handling bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import AWSProperty

# Define a simple property with an optional string field
class TestProperty(AWSProperty):
    props = {
        "OptionalField": (str, False),  # False means optional
    }

# Test 1: Valid string value should work
print("Test 1: Valid string value")
try:
    prop = TestProperty(OptionalField="test")
    print(f"Success: Created property with OptionalField='test'")
except Exception as e:
    print(f"Failed: {e}")

# Test 2: Omitting optional field should work
print("\nTest 2: Omitting optional field")
try:
    prop = TestProperty()
    print(f"Success: Created property without OptionalField")
except Exception as e:
    print(f"Failed: {e}")

# Test 3: None for optional field - should this work?
print("\nTest 3: None for optional field")
try:
    prop = TestProperty(OptionalField=None)
    print(f"Success: Created property with OptionalField=None")
except TypeError as e:
    print(f"BUG: Raised TypeError for None on optional field: {e}")