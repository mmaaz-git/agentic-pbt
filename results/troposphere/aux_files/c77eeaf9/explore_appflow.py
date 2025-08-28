#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python

import inspect
import sys
import os

# Add path and import
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.appflow as appflow

print("Module location:", appflow.__file__)
print("\n=== Public Members ===\n")

members = inspect.getmembers(appflow, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else True)

classes = []
functions = []
constants = []

for name, obj in members:
    if not name.startswith('_'):
        if inspect.isclass(obj):
            classes.append((name, obj))
        elif inspect.isfunction(obj):
            functions.append((name, obj))
        elif not inspect.ismodule(obj):
            constants.append((name, obj))

print(f"Classes ({len(classes)}):")
for name, cls in classes[:10]:  # First 10 to avoid too much output
    print(f"  - {name}")
    if hasattr(cls, '__doc__') and cls.__doc__:
        doc = cls.__doc__.strip()[:100]
        if doc:
            print(f"    Doc: {doc}...")

if len(classes) > 10:
    print(f"  ... and {len(classes) - 10} more classes")

print(f"\nFunctions ({len(functions)}):")
for name, func in functions:
    print(f"  - {name}")
    try:
        sig = inspect.signature(func)
        print(f"    Signature: {sig}")
    except:
        pass

print(f"\nConstants ({len(constants)}):")
for name, value in constants[:5]:
    print(f"  - {name}: {type(value).__name__}")