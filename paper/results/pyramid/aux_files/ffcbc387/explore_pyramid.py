#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import inspect
import pyramid

print("Pyramid module location:", pyramid.__file__)
print("\nPyramid version:", pyramid.__version__ if hasattr(pyramid, '__version__') else 'Unknown')

print("\nPublic members of pyramid module:")
members = inspect.getmembers(pyramid)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

# Group by type
functions = []
classes = []
modules = []
other = []

for name, obj in public_members:
    if inspect.isfunction(obj):
        functions.append(name)
    elif inspect.isclass(obj):
        classes.append(name)
    elif inspect.ismodule(obj):
        modules.append(name)
    else:
        other.append(name)

print(f"\nFunctions ({len(functions)}):", functions[:10] if len(functions) > 10 else functions)
print(f"\nClasses ({len(classes)}):", classes[:10] if len(classes) > 10 else classes)
print(f"\nModules ({len(modules)}):", modules[:10] if len(modules) > 10 else modules)
print(f"\nOther ({len(other)}):", other[:10] if len(other) > 10 else other)