#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import diskcache.core
import inspect

# Get all public classes and functions
members = inspect.getmembers(diskcache.core)
classes = [(name, obj) for name, obj in members if inspect.isclass(obj) and not name.startswith('_')]
functions = [(name, obj) for name, obj in members if inspect.isfunction(obj) and not name.startswith('_')]

print('PUBLIC CLASSES:')
for name, cls in classes:
    print(f'  {name}')
    
print('\nPUBLIC FUNCTIONS:')
for name, func in functions:
    print(f'  {name}')

print('\nCACHE CLASS METHODS:')
cache_methods = [m for m in dir(diskcache.core.Cache) if not m.startswith('_')]
for method in cache_methods:
    print(f'  {method}')

print('\nDISK CLASS METHODS:')
disk_methods = [m for m in dir(diskcache.core.Disk) if not m.startswith('_')]
for method in disk_methods:
    print(f'  {method}')