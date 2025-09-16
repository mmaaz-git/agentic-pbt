#!/usr/bin/env python3
"""Introspect copier.subproject module to understand its structure."""

import inspect
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from functools import cached_property
import copier._subproject as subproject

# Get all public members
print("=== Module Members ===")
members = inspect.getmembers(subproject, lambda x: not inspect.ismodule(x))
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")

print("\n=== Subproject Class Details ===")
if hasattr(subproject, 'Subproject'):
    cls = subproject.Subproject
    print(f"Class: {cls.__name__}")
    print(f"Module: {cls.__module__}")
    
    # Get class methods and properties
    print("\nMethods and properties:")
    for name in dir(cls):
        if not name.startswith('__'):
            attr = getattr(cls, name, None)
            if callable(attr):
                try:
                    sig = inspect.signature(attr)
                    print(f"  {name}{sig}")
                except (ValueError, TypeError):
                    print(f"  {name}()")
            elif isinstance(attr, property):
                print(f"  {name} (property)")
            elif isinstance(attr, cached_property):
                print(f"  {name} (cached_property)")
                
    # Get constructor signature
    print("\nConstructor:")
    try:
        sig = inspect.signature(cls.__init__)
        print(f"  __init__{sig}")
    except (ValueError, TypeError):
        print("  __init__()")
        
    # Get docstring
    if cls.__doc__:
        print(f"\nDocstring:\n{cls.__doc__}")