#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward.contents

# Get all public classes/functions
members = inspect.getmembers(awkward.contents, inspect.isclass)

print("=== Classes in awkward.contents ===")
for name, cls in members:
    if not name.startswith('_'):
        print(f"\n{name}:")
        print(f"  Module: {cls.__module__}")
        try:
            sig = inspect.signature(cls.__init__)
            print(f"  __init__ signature: {sig}")
        except:
            pass
        
        # Get docstring
        if cls.__doc__:
            doc_lines = cls.__doc__.strip().split('\n')
            print(f"  Docstring (first 3 lines):")
            for line in doc_lines[:3]:
                print(f"    {line}")

# Get source files
print("\n=== Source file locations ===")
for name, cls in members:
    if not name.startswith('_'):
        try:
            file = inspect.getfile(cls)
            print(f"{name}: {file}")
        except:
            pass