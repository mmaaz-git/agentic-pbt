#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint
import inspect
import os

# Get module info
print('Module file:', orbax.checkpoint.__file__)
print('Module path:', os.path.dirname(orbax.checkpoint.__file__))
print()

# Get public members
members = inspect.getmembers(orbax.checkpoint)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

# Categorize members
classes = []
functions = []
modules = []
other = []

for name, obj in public_members:
    if inspect.isclass(obj):
        classes.append(name)
    elif inspect.isfunction(obj):
        functions.append(name)
    elif inspect.ismodule(obj):
        modules.append(name)
    else:
        other.append(name)

print(f'Classes ({len(classes)}):')
for c in classes[:20]:  # Show first 20
    print(f'  - {c}')
print()

print(f'Functions ({len(functions)}):')
for f in functions[:20]:
    print(f'  - {f}')
print()

print(f'Modules ({len(modules)}):')
for m in modules[:20]:
    print(f'  - {m}')