#!/usr/bin/env python3
"""Investigate the numeric title bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotevents as iotevents

# Test with different titles
test_titles = ['0', '123', 'A', 'A123', 'Test123', '1A']

for title in test_titles:
    print(f"\nTesting with title: '{title}'")
    try:
        attr = iotevents.Attribute(JsonPath="/test")
        input_def = iotevents.InputDefinition(Attributes=[attr])
        obj = iotevents.Input(
            title=title,
            InputDefinition=input_def
        )
        dict_repr = obj.to_dict()
        
        # Check if title is in the dict
        if title in dict_repr:
            print(f"  ✓ Title '{title}' is in dict_repr")
            print(f"    Keys under title: {list(dict_repr[title].keys())}")
        else:
            print(f"  ✗ Title '{title}' is NOT in dict_repr")
            print(f"    Top-level keys: {list(dict_repr.keys())}")
            
        # Check the object's internal state
        print(f"    obj.title = {obj.title}")
        print(f"    obj.resource = {obj.resource}")
        
    except Exception as e:
        print(f"  Exception: {e}")

# Let's also test with a Template to see if that makes a difference
print("\n\n=== Testing with Template ===")
from troposphere import Template

template = Template()

for title in ['0', 'A0']:
    print(f"\nAdding resource with title: '{title}'")
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title=title,
        InputDefinition=input_def
    )
    template.add_resource(obj)

print("\nTemplate JSON:")
print(template.to_json())