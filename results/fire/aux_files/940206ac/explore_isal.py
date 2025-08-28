#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import inspect
import isal.isal_zlib

print("Module location:", isal.isal_zlib.__file__)
print("\nModule docstring:")
print(isal.isal_zlib.__doc__)

print("\nAll public members:")
members = inspect.getmembers(isal.isal_zlib, lambda x: not inspect.ismodule(x))
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

for name, obj in public_members:
    if inspect.isfunction(obj) or inspect.isbuiltin(obj) or inspect.isclass(obj):
        print(f"\n{name}: {type(obj).__name__}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Doc: {obj.__doc__[:200]}...")