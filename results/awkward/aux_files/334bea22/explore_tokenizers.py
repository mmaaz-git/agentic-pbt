#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.normalizers
import inspect

print("=== tokenizers.normalizers module ===")
print(f"Module file: {tokenizers.normalizers.__file__}")
print(f"Module doc: {tokenizers.normalizers.__doc__}")

print("\n=== Members of tokenizers.normalizers ===")
members = inspect.getmembers(tokenizers.normalizers, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else True)
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj)}")

# Get more details about classes
print("\n=== Classes in tokenizers.normalizers ===")
for name, obj in members:
    if not name.startswith('_') and inspect.isclass(obj):
        print(f"\n--- {name} ---")
        print(f"Doc: {obj.__doc__}")
        if hasattr(obj, '__init__'):
            try:
                sig = inspect.signature(obj.__init__)
                print(f"Signature: {sig}")
            except:
                print("Signature: Could not get signature")