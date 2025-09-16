#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import inspect
import optax

print("=== Optax Module Overview ===")
print(f"Module location: {optax.__file__}")

# Get all public members
members = inspect.getmembers(optax)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

# Categorize members
functions = []
classes = []
modules = []
other = []

for name, obj in public_members:
    if inspect.isfunction(obj):
        functions.append((name, obj))
    elif inspect.isclass(obj):
        classes.append((name, obj))
    elif inspect.ismodule(obj):
        modules.append((name, obj))
    else:
        other.append((name, obj))

print(f"\nFound {len(functions)} functions, {len(classes)} classes, {len(modules)} submodules")

# Show first 10 functions with signatures
print("\n=== Key Functions ===")
for name, func in functions[:10]:
    try:
        sig = inspect.signature(func)
        doc = func.__doc__
        if doc:
            doc_first_line = doc.split('\n')[0][:60]
        else:
            doc_first_line = "No documentation"
        print(f"  {name}{sig}: {doc_first_line}")
    except:
        print(f"  {name}: <could not get signature>")

# Show first 10 classes
print("\n=== Key Classes ===")
for name, cls in classes[:10]:
    doc = cls.__doc__
    if doc:
        doc_first_line = doc.split('\n')[0][:60]
    else:
        doc_first_line = "No documentation"
    print(f"  {name}: {doc_first_line}")

# Look for interesting modules for testing
print("\n=== Submodules ===")
for name, mod in modules[:10]:
    if hasattr(mod, '__file__'):
        print(f"  {name}: {mod.__file__}")