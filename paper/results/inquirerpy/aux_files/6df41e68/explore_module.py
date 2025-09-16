#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import inspect
import InquirerPy.prompts as target_module

# Get the module file location
print(f"Module file: {target_module.__file__}")
print(f"Module doc: {target_module.__doc__}")
print()

# Get all public members
members = inspect.getmembers(target_module)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print("Public members in InquirerPy.prompts:")
for name, obj in public_members:
    obj_type = type(obj).__name__
    if inspect.isfunction(obj) or inspect.isclass(obj):
        try:
            sig = inspect.signature(obj)
            print(f"  {name} ({obj_type}): {sig}")
            if obj.__doc__:
                print(f"    Docstring: {obj.__doc__[:100]}...")
        except:
            print(f"  {name} ({obj_type})")
    else:
        print(f"  {name} ({obj_type})")
print()

# Check for imports from __init__.py
print("Checking what's imported in __init__.py:")
init_file = target_module.__file__
with open(init_file, 'r') as f:
    print(f.read())