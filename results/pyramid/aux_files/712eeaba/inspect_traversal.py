#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal

# Get all public functions/classes in the module
public_members = [(name, obj) for name, obj in inspect.getmembers(traversal) 
                  if not name.startswith('_') and (inspect.isfunction(obj) or inspect.isclass(obj))]

print("=== Public Functions and Classes in pyramid.traversal ===\n")

for name, obj in public_members:
    if inspect.isfunction(obj):
        print(f"Function: {name}")
        try:
            sig = inspect.signature(obj)
            print(f"  Signature: {name}{sig}")
        except:
            print(f"  Signature: Could not determine")
        
        if obj.__doc__:
            # Print just the first line of the docstring
            doc_lines = obj.__doc__.strip().split('\n')
            print(f"  Description: {doc_lines[0]}")
        print()
    elif inspect.isclass(obj):
        print(f"Class: {name}")
        print()

print("\n=== Key Functions to Test ===")
key_functions = [
    'find_root', 'find_resource', 'resource_path', 'resource_path_tuple',
    'traverse', 'traversal_path', 'traversal_path_info', 'split_path_info',
    'quote_path_segment', 'virtual_root'
]

for fname in key_functions:
    if hasattr(traversal, fname):
        func = getattr(traversal, fname)
        if func.__doc__:
            doc_lines = func.__doc__.strip().split('\n')
            print(f"{fname}: {doc_lines[0]}")