#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.tools

# Get all members of the module
members = inspect.getmembers(tokenizers.tools)

print("=== Module Members ===")
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"{name}: {obj_type}")
        
        # If it's a function or class, show more info
        if inspect.isfunction(obj) or inspect.isclass(obj):
            try:
                sig = inspect.signature(obj)
                print(f"  Signature: {sig}")
            except:
                pass
            if hasattr(obj, '__doc__') and obj.__doc__:
                doc = obj.__doc__.split('\n')[0][:100]
                print(f"  Doc: {doc}")

print("\n=== Module File Path ===")
print(tokenizers.tools.__file__)

print("\n=== Submodules ===")
import os
module_dir = os.path.dirname(tokenizers.tools.__file__)
for item in os.listdir(module_dir):
    if item.endswith('.py') or os.path.isdir(os.path.join(module_dir, item)):
        print(f"  {item}")