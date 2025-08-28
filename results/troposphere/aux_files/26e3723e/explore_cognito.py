#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.cognito as cognito

# Get module file location
print(f"Module file: {cognito.__file__}")

# Get all public classes and functions
members = inspect.getmembers(cognito, lambda x: (inspect.isclass(x) or inspect.isfunction(x)) and not x.__name__.startswith('_'))

print(f"\nTotal public members: {len(members)}")
print("\nPublic classes and functions:")
for name, obj in members:
    if inspect.isclass(obj):
        # Check if it's defined in this module
        if obj.__module__ == 'troposphere.cognito':
            print(f"  Class: {name}")
            # Get __init__ signature if available
            try:
                sig = inspect.signature(obj.__init__)
                print(f"    Signature: {sig}")
            except:
                pass
    elif inspect.isfunction(obj):
        print(f"  Function: {name}")
        try:
            sig = inspect.signature(obj)
            print(f"    Signature: {sig}")
        except:
            pass

# List the first few classes in detail
print("\n\nDetailed view of some classes:")
for name, obj in members[:5]:
    if inspect.isclass(obj) and obj.__module__ == 'troposphere.cognito':
        print(f"\n{name}:")
        if obj.__doc__:
            print(f"  Docstring: {obj.__doc__[:200]}...")
        # Get class attributes
        attrs = [a for a in dir(obj) if not a.startswith('_')]
        print(f"  Attributes: {attrs[:10]}")