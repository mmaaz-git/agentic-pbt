#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import inspect
import spnego.ntlm

# Get module file
print(f"Module file: {spnego.ntlm.__file__}")
print()

# Get all members
members = inspect.getmembers(spnego.ntlm)
print("Public members of spnego.ntlm:")
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")
print()

# Look for functions and classes
print("Functions and classes:")
for name, obj in members:
    if not name.startswith('_'):
        if inspect.isfunction(obj) or inspect.isclass(obj):
            print(f"\n{name} ({type(obj).__name__}):")
            if hasattr(obj, '__doc__') and obj.__doc__:
                print(f"  Docstring: {obj.__doc__[:200]}...")
            if inspect.isfunction(obj):
                try:
                    sig = inspect.signature(obj)
                    print(f"  Signature: {sig}")
                except:
                    pass