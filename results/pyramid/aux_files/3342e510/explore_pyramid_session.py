#!/usr/bin/env python3
"""Explore pyramid.session module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import inspect
import pyramid.session

# Get module file location
print(f"Module file: {pyramid.session.__file__}")
print(f"Module path: {pyramid.session.__path__ if hasattr(pyramid.session, '__path__') else 'N/A'}")
print()

# Get all public members
members = inspect.getmembers(pyramid.session, lambda x: not (inspect.ismodule(x) or x.__name__.startswith('_') if hasattr(x, '__name__') else False))

print("Public members of pyramid.session:")
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")
        
print("\n" + "="*60 + "\n")

# Get classes specifically
classes = inspect.getmembers(pyramid.session, inspect.isclass)
print("Classes in pyramid.session:")
for name, cls in classes:
    if not name.startswith('_'):
        print(f"\n{name}:")
        # Show docstring
        if cls.__doc__:
            print(f"  Docstring: {cls.__doc__[:200]}...")
        # Show methods
        methods = [m for m in dir(cls) if not m.startswith('_')]
        print(f"  Public methods: {methods[:10]}")  # First 10 methods
        
print("\n" + "="*60 + "\n")

# Get functions
functions = inspect.getmembers(pyramid.session, inspect.isfunction)
print("Functions in pyramid.session:")
for name, func in functions:
    if not name.startswith('_'):
        print(f"\n{name}:")
        sig = inspect.signature(func)
        print(f"  Signature: {sig}")
        if func.__doc__:
            print(f"  Docstring: {func.__doc__[:200]}...")