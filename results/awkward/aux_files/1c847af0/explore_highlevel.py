#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import inspect
import awkward
import awkward.highlevel

# Get all public members of awkward.highlevel module
members = inspect.getmembers(awkward.highlevel)

# Filter to get functions and classes
functions = []
classes = []
for name, obj in members:
    if not name.startswith('_'):
        if inspect.isfunction(obj):
            functions.append((name, obj))
        elif inspect.isclass(obj):
            classes.append((name, obj))

print("Classes in awkward.highlevel:")
for name, cls in classes:
    print(f"  - {name}")
    # Get key methods
    methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
    if methods[:10]:  # Show first 10 methods
        print(f"    Methods: {', '.join(methods[:10])}")

print("\nFunctions in awkward.highlevel:")
for name, func in functions[:20]:  # Show first 20 functions
    sig = inspect.signature(func) if hasattr(func, '__wrapped__') else "..."
    print(f"  - {name}{sig}")

# Let's also check the main Array class
print("\nArray class info:")
print(f"  File: {inspect.getfile(awkward.highlevel.Array)}")

# Get some key Array methods
array_methods = [m for m in dir(awkward.highlevel.Array) if not m.startswith('_')]
print(f"\nArray public methods/properties ({len(array_methods)} total):")
for method in array_methods[:30]:
    print(f"  - {method}")