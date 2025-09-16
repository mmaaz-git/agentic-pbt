#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.request

# Get module file location
print(f"Module file: {pyramid.request.__file__}")
print()

# Get all public functions and classes
members = inspect.getmembers(pyramid.request)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print("Public classes and functions:")
for name, obj in public_members:
    if inspect.isclass(obj):
        print(f"  Class: {name}")
        # Get methods of the class
        methods = inspect.getmembers(obj, predicate=inspect.ismethod)
        functions = inspect.getmembers(obj, predicate=inspect.isfunction) 
        all_methods = methods + functions
        public_methods = [(m_name, m_obj) for m_name, m_obj in all_methods if not m_name.startswith('_')]
        if public_methods:
            for method_name, _ in public_methods[:5]:  # Show first 5 methods
                print(f"    - {method_name}")
            if len(public_methods) > 5:
                print(f"    ... and {len(public_methods) - 5} more")
    elif inspect.isfunction(obj):
        print(f"  Function: {name}")
    elif not inspect.ismodule(obj) and not inspect.isbuiltin(obj):
        print(f"  {type(obj).__name__}: {name}")
print()

# Look specifically for the Request class
if hasattr(pyramid.request, 'Request'):
    Request = pyramid.request.Request
    print("Request class found!")
    print(f"  Docstring: {Request.__doc__[:200] if Request.__doc__ else 'No docstring'}...")
    print(f"  MRO: {[cls.__name__ for cls in Request.__mro__[:3]]}")