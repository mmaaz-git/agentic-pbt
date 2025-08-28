#!/usr/bin/env python3
"""Test title type validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotevents as iotevents
from troposphere import Template

# Test that shows the bug
print("Demonstrating the bug:")
print("=" * 50)

# This should fail but doesn't
print("\nTest 1: Integer 0 as title (should fail but doesn't):")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title=0,  # This is an integer, not a string!
        InputDefinition=input_def
    )
    print(f"  Created object with integer title: {obj.title} (type: {type(obj.title).__name__})")
    
    # Try to use it in a template
    template = Template()
    template.add_resource(obj)
    json_output = template.to_json()
    print(f"  Template JSON created successfully")
    print(f"  Resources keys: {list(template.resources.keys())}")
    
except Exception as e:
    print(f"  Exception: {e}")

# This fails with a confusing error
print("\nTest 2: Integer 123 as title (fails with confusing error):")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title=123,  # This is an integer, not a string!
        InputDefinition=input_def
    )
    print(f"  Created object with integer title: {obj.title}")
except Exception as e:
    print(f"  Exception: {e}")

# What about None?
print("\nTest 3: None as title:")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title=None,
        InputDefinition=input_def
    )
    print(f"  Created object with None title: {obj.title}")
    
    # Try to convert to dict
    d = obj.to_dict()
    print(f"  to_dict() succeeded")
    
except Exception as e:
    print(f"  Exception: {e}")

# What about empty string?
print("\nTest 4: Empty string as title:")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title="",
        InputDefinition=input_def
    )
    print(f"  Created object with empty string title: {repr(obj.title)}")
    d = obj.to_dict()
    print(f"  to_dict() succeeded")
except Exception as e:
    print(f"  Exception: {e}")

# Test with boolean
print("\nTest 5: Boolean True as title:")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title=True,
        InputDefinition=input_def
    )
    print(f"  Created object with boolean title: {obj.title} (type: {type(obj.title).__name__})")
except Exception as e:
    print(f"  Exception: {e}")

print("\nTest 6: Boolean False as title:")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title=False,
        InputDefinition=input_def
    )
    print(f"  Created object with boolean title: {obj.title} (type: {type(obj.title).__name__})")
    
    # Try to use it in a template
    template = Template()
    template.add_resource(obj)
    json_output = template.to_json()
    print(f"  Template JSON created successfully")
    print(f"  Resources keys: {list(template.resources.keys())}")
    
except Exception as e:
    print(f"  Exception: {e}")