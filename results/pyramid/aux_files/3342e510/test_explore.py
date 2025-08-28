#!/usr/bin/env python3
import sys
import inspect
import os

try:
    import pyramid.csrf
    print("Successfully imported pyramid.csrf")
    
    # Get module file location
    csrf_file = pyramid.csrf.__file__
    print(f"Module file: {csrf_file}")
    
    # Get all members of the module
    members = inspect.getmembers(pyramid.csrf)
    
    print("\nPublic functions and classes in pyramid.csrf:")
    for name, obj in members:
        if not name.startswith('_'):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                print(f"  - {name}: {type(obj).__name__}")
                if hasattr(obj, '__doc__') and obj.__doc__:
                    doc_lines = obj.__doc__.strip().split('\n')
                    if doc_lines:
                        print(f"    Doc: {doc_lines[0][:80]}...")
    
    # Check module docstring
    if pyramid.csrf.__doc__:
        print(f"\nModule docstring: {pyramid.csrf.__doc__[:200]}...")
        
except ImportError as e:
    print(f"Failed to import pyramid.csrf: {e}")
    sys.exit(1)