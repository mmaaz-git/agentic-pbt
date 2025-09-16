#!/usr/bin/env python3
import sys
import inspect
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy.tokenizer as tokenizer

print("Module file:", tokenizer.__file__)
print("\nModule directory:", os.path.dirname(tokenizer.__file__))
print("\nAll members in module:")
members = inspect.getmembers(tokenizer)
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")
        
print("\nLet's look at classes and functions in more detail:")
for name, obj in members:
    if not name.startswith('_'):
        if inspect.isclass(obj):
            print(f"\nClass: {name}")
            if obj.__doc__:
                print(f"  Docstring: {obj.__doc__[:200]}...")
            # Get class methods
            methods = [m for m in dir(obj) if not m.startswith('_')]
            if methods:
                print(f"  Public methods: {methods[:10]}")
        elif inspect.isfunction(obj):
            print(f"\nFunction: {name}")
            if obj.__doc__:
                print(f"  Docstring: {obj.__doc__[:200]}...")
            try:
                sig = inspect.signature(obj)
                print(f"  Signature: {sig}")
            except:
                pass