#!/usr/bin/env python3
"""
Exploratory script to understand awkward.cppyy module
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

# First, let's see what's available in awkward.cppyy
import awkward.cppyy
import inspect

print("=== awkward.cppyy module contents ===")
members = inspect.getmembers(awkward.cppyy)
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                print(f"  Signature: {sig}")
            except:
                pass
            if obj.__doc__:
                print(f"  Doc: {obj.__doc__[:200]}")

# Check the register_and_check function
print("\n=== Testing register_and_check function ===")
print(f"Function exists: {hasattr(awkward.cppyy, 'register_and_check')}")

# Let's also look at _connect.cling which seems related
print("\n=== awkward._connect.cling module ===")
from awkward._connect import cling
cling_members = inspect.getmembers(cling)
functions = []
classes = []
for name, obj in cling_members:
    if not name.startswith('_'):
        if inspect.isfunction(obj):
            functions.append(name)
        elif inspect.isclass(obj):
            classes.append(name)

print(f"Functions: {functions[:10]}")  # First 10
print(f"Classes: {classes[:10]}")  # First 10

# Check togenerator function
if 'togenerator' in functions:
    print(f"\ntogenerator signature: {inspect.signature(cling.togenerator)}")

# Check generator classes
for cls_name in ['NumpyArrayGenerator', 'ListArrayGenerator', 'RecordArrayGenerator']:
    if cls_name in classes:
        cls = getattr(cling, cls_name)
        print(f"\n{cls_name}:")
        print(f"  __init__ signature: {inspect.signature(cls.__init__)}")
        methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
        print(f"  Methods: {methods[:5]}")