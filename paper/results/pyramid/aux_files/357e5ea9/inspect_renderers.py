#!/usr/bin/env python3
import inspect
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.renderers as renderers

# Get all public classes and functions
members = inspect.getmembers(renderers)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print('=== Public API of pyramid.renderers ===')
print()

functions = []
classes = []
other = []

for name, obj in public_members:
    if inspect.isclass(obj):
        classes.append((name, obj))
    elif inspect.isfunction(obj):
        functions.append((name, obj))
    else:
        other.append((name, obj))

print('Functions:')
for name, obj in functions:
    sig = inspect.signature(obj) if hasattr(inspect, 'signature') else ''
    print(f'  {name}{sig}')
    if obj.__doc__:
        first_line = obj.__doc__.split('\n')[0] if obj.__doc__ else ''
        print(f'    {first_line[:80]}')

print('\nClasses:')
for name, obj in classes:
    print(f'  {name}')
    if obj.__doc__:
        first_line = obj.__doc__.split('\n')[0] if obj.__doc__ else ''
        print(f'    {first_line[:80]}')

print('\nOther:')
for name, obj in other[:10]:  # Limit to first 10
    print(f'  {name}: {type(obj).__name__}')