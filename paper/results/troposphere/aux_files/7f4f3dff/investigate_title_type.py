#!/usr/bin/env python3
"""Investigate title type conversion issue"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotevents as iotevents

# Test with numeric string titles
test_titles = ['0', '123', '001', '1.5', '-1']

for title_str in test_titles:
    print(f"\nTesting with title string: '{title_str}'")
    try:
        attr = iotevents.Attribute(JsonPath="/test")
        input_def = iotevents.InputDefinition(Attributes=[attr])
        obj = iotevents.Input(
            title=title_str,
            InputDefinition=input_def
        )
        
        print(f"  obj.title = {repr(obj.title)} (type: {type(obj.title).__name__})")
        
        # Check if the title validation is working correctly
        if isinstance(obj.title, str):
            print(f"  Title is correctly a string")
        else:
            print(f"  BUG: Title was converted from string to {type(obj.title).__name__}")
            
    except Exception as e:
        print(f"  Exception: {e}")

# Also test what happens if we pass an integer directly
print("\n\n=== Testing with integer titles ===")
for title_int in [0, 123]:
    print(f"\nTesting with integer title: {title_int}")
    try:
        attr = iotevents.Attribute(JsonPath="/test")
        input_def = iotevents.InputDefinition(Attributes=[attr])
        obj = iotevents.Input(
            title=title_int,
            InputDefinition=input_def
        )
        print(f"  obj.title = {repr(obj.title)} (type: {type(obj.title).__name__})")
    except Exception as e:
        print(f"  Exception: {e}")