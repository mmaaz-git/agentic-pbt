#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.kendra as kendra

# Get all classes and functions
members = inspect.getmembers(kendra)

# Separate AWSProperty and AWSObject classes
aws_properties = []
aws_objects = []
other_items = []

for name, obj in members:
    if inspect.isclass(obj):
        if hasattr(obj, '__bases__'):
            bases = [b.__name__ for b in obj.__bases__]
            if 'AWSProperty' in bases:
                aws_properties.append((name, obj))
            elif 'AWSObject' in bases:
                aws_objects.append((name, obj))
            else:
                other_items.append((name, obj))
    elif not name.startswith('_'):
        other_items.append((name, obj))

print("=== AWS Objects (Resources) ===")
for name, obj in aws_objects:
    print(f"- {name}")
    if hasattr(obj, 'resource_type'):
        print(f"  Resource Type: {obj.resource_type}")
    if hasattr(obj, 'props'):
        print(f"  Properties: {len(obj.props)} props")

print("\n=== AWS Properties ===")
print(f"Total: {len(aws_properties)} property classes")
for name, obj in aws_properties[:5]:  # Show first 5
    print(f"- {name}")
    if hasattr(obj, 'props'):
        print(f"  Fields: {list(obj.props.keys())}")

print("\n=== Other items ===")
for name, obj in other_items[:10]:
    print(f"- {name}: {type(obj)}")