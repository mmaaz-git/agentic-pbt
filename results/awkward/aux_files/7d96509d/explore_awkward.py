#!/usr/bin/env python3
import sys
import os
import inspect

# Add the awkward env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

# Look at the Array class
print("Array class:")
print(f"  Signature: {inspect.signature(ak.Array)}")
print(f"  Docstring preview: {ak.Array.__doc__[:500] if ak.Array.__doc__ else 'No docstring'}")

# Look at some core functions
functions_to_explore = ['concatenate', 'cartesian', 'argsort', 'zip', 'unzip', 'flatten', 'fill_none', 'is_none', 'pad_none', 'mask']

print("\n\nCore functions:")
for func_name in functions_to_explore:
    if hasattr(ak, func_name):
        func = getattr(ak, func_name)
        try:
            sig = inspect.signature(func)
            print(f"\n{func_name}:")
            print(f"  Signature: {sig}")
            if func.__doc__:
                # Get the first meaningful line of the docstring
                lines = [line.strip() for line in func.__doc__.split('\n') if line.strip()]
                if lines:
                    print(f"  Doc: {lines[0][:200]}")
        except Exception as e:
            print(f"\n{func_name}: Could not get signature ({e})")

# Get the file location for the main implementation
print(f"\n\nMain implementation file: {inspect.getfile(ak.Array)}")