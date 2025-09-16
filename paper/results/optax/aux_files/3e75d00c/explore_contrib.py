#!/usr/bin/env python3
import optax.contrib
import inspect
import types

# Get all members of optax.contrib
members = inspect.getmembers(optax.contrib)

# Filter out functions and classes
public_members = []
for name, obj in members:
    if not name.startswith('_'):
        if inspect.isfunction(obj) or inspect.isclass(obj):
            public_members.append((name, type(obj).__name__))

print('Public functions and classes in optax.contrib:')
for name, obj_type in sorted(public_members):
    print(f'  {name}: {obj_type}')

# Get the module file location
print(f'\nModule file location: {optax.contrib.__file__}')