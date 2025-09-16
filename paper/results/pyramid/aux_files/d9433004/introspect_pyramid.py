import sys
import inspect
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.httpexceptions as target_module

print("=== Module Analysis: pyramid.httpexceptions ===\n")
print(f"Module file: {target_module.__file__}")
print(f"Module directory: {os.path.dirname(target_module.__file__)}")

print("\n=== Public Classes and Functions ===")
members = inspect.getmembers(target_module)
classes = []
functions = []
constants = []

for name, obj in members:
    if name.startswith('_'):
        continue
    if inspect.isclass(obj):
        classes.append((name, obj))
    elif inspect.isfunction(obj):
        functions.append((name, obj))
    elif not inspect.ismodule(obj):
        constants.append((name, obj))

print(f"\nFound {len(classes)} public classes")
for name, cls in classes[:10]:
    print(f"  {name}: {cls.__doc__.split('\\n')[0] if cls.__doc__ else 'No docstring'}")

print(f"\nFound {len(functions)} public functions")
for name, func in functions[:10]:
    sig = inspect.signature(func)
    print(f"  {name}{sig}: {func.__doc__.split('\\n')[0] if func.__doc__ else 'No docstring'}")

print(f"\nConstants/Variables: {[name for name, _ in constants[:20]]}")