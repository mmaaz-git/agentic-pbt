#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.pinpointemail as pe

# Get all classes in the module
all_members = inspect.getmembers(pe, inspect.isclass)
print("Classes in troposphere.pinpointemail:")
for name, cls in all_members:
    if cls.__module__ == 'troposphere.pinpointemail':
        print(f"\n{name}:")
        print(f"  Base classes: {[base.__name__ for base in cls.__bases__]}")
        if hasattr(cls, 'props'):
            print(f"  Properties: {list(cls.props.keys())}")
        if hasattr(cls, 'resource_type'):
            print(f"  Resource type: {cls.resource_type}")

# Inspect key parent classes
from troposphere import AWSObject, AWSProperty
print("\n\nAWSObject base class:")
print(f"  Module: {AWSObject.__module__}")
print(f"  Methods: {[m for m in dir(AWSObject) if not m.startswith('_')]}")

print("\n\nAWSProperty base class:")
print(f"  Module: {AWSProperty.__module__}")
print(f"  Methods: {[m for m in dir(AWSProperty) if not m.startswith('_')]}")

# Check validators module
from troposphere.validators import boolean
print(f"\n\nBoolean validator type: {type(boolean)}")
print(f"Boolean validator: {boolean}")