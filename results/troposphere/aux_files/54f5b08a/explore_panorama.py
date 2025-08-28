#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.panorama as panorama

# Get all public members
print("=== Public members of troposphere.panorama ===")
members = inspect.getmembers(panorama, lambda x: not inspect.ismodule(x))
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")

print("\n=== Classes and their properties ===")
# Focus on classes
classes = [m for m in members if not m[0].startswith('_') and inspect.isclass(m[1])]
for class_name, cls in classes:
    print(f"\n{class_name}:")
    if hasattr(cls, '__doc__') and cls.__doc__:
        print(f"  Doc: {cls.__doc__.strip()[:100]}...")
    if hasattr(cls, 'props'):
        print(f"  Props: {cls.props}")
    if hasattr(cls, 'resource_type'):
        print(f"  Resource Type: {cls.resource_type}")
    
    # Check parent classes
    print(f"  Parent classes: {[parent.__name__ for parent in cls.__bases__]}")
    
    # Check methods
    methods = [m for m in inspect.getmembers(cls) if inspect.ismethod(m[1]) or inspect.isfunction(m[1])]
    public_methods = [m[0] for m in methods if not m[0].startswith('_')]
    if public_methods:
        print(f"  Public methods: {public_methods}")