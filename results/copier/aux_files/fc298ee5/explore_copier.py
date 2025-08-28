#!/usr/bin/env python3
import sys
import inspect
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier.main
import copier._main

# Get all public functions and classes
print("=== Public members in copier.main ===")
for name, obj in inspect.getmembers(copier.main):
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")

print("\n=== Public members in copier._main ===")
public_members = []
for name, obj in inspect.getmembers(copier._main):
    if not name.startswith('_'):
        if inspect.isfunction(obj) or inspect.isclass(obj):
            public_members.append((name, obj))
            print(f"{name}: {type(obj).__name__}")

print("\n=== Main functions signatures ===")
# Focus on the main functions
main_funcs = ['run_copy', 'run_recopy', 'run_update']
for func_name in main_funcs:
    func = getattr(copier._main, func_name, None)
    if func:
        print(f"\n{func_name}:")
        print(f"  Signature: {inspect.signature(func)}")
        if func.__doc__:
            print(f"  Doc: {func.__doc__[:200]}...")

# Look at the Worker class
print("\n=== Worker class methods ===")
worker_class = copier._main.Worker
for name, method in inspect.getmembers(worker_class):
    if not name.startswith('_') and callable(method):
        print(f"  {name}")

# Check if there are any interesting helper functions
print("\n=== Other important functions ===")
for name, obj in public_members:
    if inspect.isfunction(obj) and name not in main_funcs:
        print(f"{name}: {inspect.signature(obj)}")