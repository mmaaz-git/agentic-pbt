#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere

# Get core classes
print("=== Core Classes ===")
for name, obj in inspect.getmembers(troposphere):
    if inspect.isclass(obj) and not name.startswith('_'):
        print(f"\n{name}:")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Doc: {obj.__doc__[:100]}...")
        
        # Show some important methods
        methods = [m for m in dir(obj) if not m.startswith('_')][:5]
        if methods:
            print(f"  Methods: {', '.join(methods)}")

# Look at helper functions
print("\n\n=== Helper Functions ===")
for name, obj in inspect.getmembers(troposphere):
    if inspect.isfunction(obj) and not name.startswith('_'):
        sig = inspect.signature(obj)
        print(f"\n{name}{sig}:")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Doc: {obj.__doc__[:100]}...")

# Look at constants
print("\n\n=== Constants ===")
for name in dir(troposphere):
    if name.isupper() and not name.startswith('_'):
        val = getattr(troposphere, name)
        print(f"{name} = {val}")