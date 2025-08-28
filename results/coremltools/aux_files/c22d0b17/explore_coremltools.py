#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import inspect
import coremltools.models

# Get all public members of the module
members = inspect.getmembers(coremltools.models)
print("=== Public members of coremltools.models ===")
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"{name}: {obj_type}")

print("\n=== Module file location ===")
print(coremltools.models.__file__)

print("\n=== Classes and Functions ===")
for name, obj in members:
    if not name.startswith('_'):
        if inspect.isclass(obj):
            print(f"\nClass: {name}")
            if hasattr(obj, '__doc__') and obj.__doc__:
                print(f"  Docstring: {obj.__doc__[:200]}...")
        elif inspect.isfunction(obj):
            print(f"\nFunction: {name}")
            try:
                sig = inspect.signature(obj)
                print(f"  Signature: {sig}")
            except:
                pass
            if hasattr(obj, '__doc__') and obj.__doc__:
                print(f"  Docstring: {obj.__doc__[:200]}...")