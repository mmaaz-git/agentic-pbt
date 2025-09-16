#!/usr/bin/env python3
import sys
import os
import inspect

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier._vcs as vcs

print("=== Public Functions in copier._vcs ===\n")

# Get all public functions/classes
members = inspect.getmembers(vcs, inspect.isfunction)
for name, func in members:
    if not name.startswith('_'):
        print(f"Function: {name}")
        try:
            sig = inspect.signature(func)
            print(f"  Signature: {sig}")
        except:
            print("  Signature: (unable to get)")
        
        doc = inspect.getdoc(func)
        if doc:
            # Print first line of docstring
            first_line = doc.split('\n')[0]
            print(f"  Doc: {first_line}")
        print()

# Also check for constants/variables
print("\n=== Constants ===")
for name in dir(vcs):
    if not name.startswith('_') and name.isupper():
        value = getattr(vcs, name)
        print(f"{name}: {value}")