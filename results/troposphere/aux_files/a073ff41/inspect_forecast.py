#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import troposphere.forecast as f
import inspect

# Get all public members
members = inspect.getmembers(f)
for name, obj in members:
    if not name.startswith('_'):
        print(f'{name}: {type(obj).__name__}')

print("\n--- Dataset class methods ---")
for name, method in inspect.getmembers(f.Dataset):
    if not name.startswith('_'):
        print(f'{name}: {type(method).__name__}')

print("\n--- DatasetGroup class methods ---")
for name, method in inspect.getmembers(f.DatasetGroup):
    if not name.startswith('_'):
        print(f'{name}: {type(method).__name__}')