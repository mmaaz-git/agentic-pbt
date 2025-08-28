#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import inspect
import spnego

# Get module file location
print(f"Module file: {spnego.__file__}")
print(f"Module version: {getattr(spnego, '__version__', 'No version attribute')}")
print(f"Module docstring: {spnego.__doc__}")
print("\n" + "="*50 + "\n")

# Get all public members
members = inspect.getmembers(spnego, lambda x: not isinstance(x, type(sys)))
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print("Public classes and functions:")
for name, obj in public_members:
    if inspect.isclass(obj):
        print(f"  Class: {name}")
        # Get class docstring
        if obj.__doc__:
            first_line = obj.__doc__.split('\n')[0] if obj.__doc__ else ""
            print(f"    Doc: {first_line[:100]}")
    elif inspect.isfunction(obj) or inspect.ismethod(obj):
        print(f"  Function: {name}")
        if obj.__doc__:
            first_line = obj.__doc__.split('\n')[0] if obj.__doc__ else ""
            print(f"    Doc: {first_line[:100]}")

print("\n" + "="*50 + "\n")

# Get submodules
import os
module_dir = os.path.dirname(spnego.__file__)
print(f"Module directory: {module_dir}")
print("Submodules/files:")
for item in os.listdir(module_dir):
    if item.endswith('.py') and not item.startswith('_'):
        print(f"  {item}")