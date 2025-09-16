#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.kafkaconnect as kafkaconnect

# Get all public classes and functions
members = inspect.getmembers(kafkaconnect, lambda x: inspect.isclass(x) or inspect.isfunction(x))
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print("=== Public classes and functions in troposphere.kafkaconnect ===")
for name, obj in public_members:
    if inspect.isclass(obj):
        print(f"\nClass: {name}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Doc: {obj.__doc__.strip()[:200]}")
        if hasattr(obj, 'props'):
            print(f"  Props: {list(obj.props.keys())}")
        # Check if it's a subclass of AWSObject or AWSProperty
        if hasattr(obj, '__bases__'):
            print(f"  Base classes: {[base.__name__ for base in obj.__bases__]}")
    elif inspect.isfunction(obj):
        print(f"\nFunction: {name}")
        sig = inspect.signature(obj)
        print(f"  Signature: {sig}")
        if obj.__doc__:
            print(f"  Doc: {obj.__doc__.strip()[:200]}")

# Let's also check the base classes
print("\n=== Base classes ===")
from troposphere import AWSObject, AWSProperty
print(f"AWSObject base: {AWSObject.__bases__}")
print(f"AWSProperty base: {AWSProperty.__bases__}")

# Get all attributes of an example class
print("\n=== Exploring ScaleInPolicy class in detail ===")
scale_in = kafkaconnect.ScaleInPolicy
print(f"Class attributes: {dir(scale_in)}")
print(f"Props: {scale_in.props}")