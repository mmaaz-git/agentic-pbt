#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

import pyatlan.generator
import inspect
import os

print(f"Successfully imported pyatlan.generator")
print(f"Type: {type(pyatlan.generator)}")
print(f"Module file: {pyatlan.generator.__file__}")

# Get all members of the module
members = inspect.getmembers(pyatlan.generator)
print("\nPublic members of pyatlan.generator:")
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")