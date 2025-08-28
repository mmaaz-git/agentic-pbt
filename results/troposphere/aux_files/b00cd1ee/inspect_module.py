#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.awslambda as awslambda

# Get all classes and functions
members = inspect.getmembers(awslambda)

print("=== Classes ===")
for name, obj in members:
    if inspect.isclass(obj) and obj.__module__ == 'troposphere.awslambda':
        print(f"\n{name}:")
        if hasattr(obj, 'props'):
            print(f"  Properties: {list(obj.props.keys())}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            docstring = obj.__doc__.strip()
            if docstring:
                print(f"  Docstring: {docstring[:100]}...")

print("\n=== Functions ===")
for name, obj in members:
    if inspect.isfunction(obj) and obj.__module__ == 'troposphere.validators.awslambda':
        print(f"\n{name}:")
        sig = inspect.signature(obj)
        print(f"  Signature: {sig}")
        if obj.__doc__:
            print(f"  Docstring: {obj.__doc__.strip()[:200]}...")

print("\n=== Constants ===")
print(f"MINIMUM_MEMORY: {awslambda.MINIMUM_MEMORY}")
print(f"MAXIMUM_MEMORY: {awslambda.MAXIMUM_MEMORY}")