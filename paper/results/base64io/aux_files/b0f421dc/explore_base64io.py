#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/base64io_env/lib/python3.13/site-packages')

import inspect
import base64io

print("Module:", base64io)
print("Module file:", base64io.__file__)
print("Module doc:", base64io.__doc__)
print()

members = inspect.getmembers(base64io)
print("Module members:")
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"    Doc: {obj.__doc__[:200]}...")
print()

# Get public classes and functions
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]
for name, obj in public_members:
    if inspect.isclass(obj):
        print(f"\nClass: {name}")
        print(f"  Signature: {inspect.signature(obj) if callable(obj) else 'N/A'}")
        print(f"  Doc: {obj.__doc__[:500] if obj.__doc__ else 'No doc'}...")
        
        # Get class methods
        class_members = inspect.getmembers(obj)
        for method_name, method in class_members:
            if not method_name.startswith('_') and callable(method):
                print(f"  Method: {method_name}")
                try:
                    print(f"    Signature: {inspect.signature(method)}")
                except:
                    pass
    elif inspect.isfunction(obj):
        print(f"\nFunction: {name}")
        print(f"  Signature: {inspect.signature(obj)}")
        print(f"  Doc: {obj.__doc__[:500] if obj.__doc__ else 'No doc'}...")