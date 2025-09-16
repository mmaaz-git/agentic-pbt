#!/usr/bin/env python3
import sys
import os
import inspect

# Add the awkward env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

print(f"Awkward version: {ak.__version__}")
print(f"Module file: {ak.__file__}")
print("\nPublic functions and classes:")

members = inspect.getmembers(ak)
functions = []
classes = []
for name, obj in members:
    if not name.startswith("_"):
        if inspect.isfunction(obj) or inspect.isbuiltin(obj):
            functions.append(name)
        elif inspect.isclass(obj):
            classes.append(name)

print(f"\nFunctions ({len(functions)}):")
for func in sorted(functions)[:20]:  # Show first 20
    print(f"  - {func}")
if len(functions) > 20:
    print(f"  ... and {len(functions) - 20} more")

print(f"\nClasses ({len(classes)}):")
for cls in sorted(classes)[:20]:  # Show first 20
    print(f"  - {cls}")
if len(classes) > 20:
    print(f"  ... and {len(classes) - 20} more")

# Look at the top-level operations module
print("\n\nTop-level operations:")
if hasattr(ak, 'operations'):
    op_members = inspect.getmembers(ak.operations)
    op_funcs = [name for name, obj in op_members if not name.startswith("_") and (inspect.isfunction(obj) or inspect.isbuiltin(obj))]
    print(f"Operations module has {len(op_funcs)} functions")
    for func in sorted(op_funcs)[:10]:
        print(f"  - {func}")