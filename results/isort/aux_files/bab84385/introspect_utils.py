import inspect
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.utils

# Get all public members of isort.utils
members = inspect.getmembers(isort.utils)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print("Public members of isort.utils:")
for name, obj in public_members:
    if inspect.isfunction(obj):
        print(f"  Function: {name}")
        sig = inspect.signature(obj)
        print(f"    Signature: {sig}")
        if obj.__doc__:
            doc_lines = obj.__doc__.strip().split('\n')
            print(f"    Doc: {doc_lines[0][:100]}")
    elif inspect.isclass(obj):
        print(f"  Class: {name}")
        if obj.__doc__:
            doc_lines = obj.__doc__.strip().split('\n') if obj.__doc__ else []
            if doc_lines:
                print(f"    Doc: {doc_lines[0][:100]}")

# Check functions in detail
print("\nFunction details:")
for name, obj in public_members:
    if inspect.isfunction(obj) and not name.startswith('_'):
        print(f"\n{name}:")
        print(f"  File: {inspect.getfile(obj)}")
        print(f"  Module: {obj.__module__}")