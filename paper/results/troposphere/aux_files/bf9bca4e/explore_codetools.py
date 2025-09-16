#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import inspect
from jurigged import codetools

# Get all public members
members = inspect.getmembers(codetools)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

# Categorize them
functions = []
classes = []
other = []

for name, obj in public_members:
    if inspect.isfunction(obj):
        functions.append((name, obj))
    elif inspect.isclass(obj):
        classes.append((name, obj))
    else:
        other.append((name, obj))

print("=== CLASSES ===")
for name, cls in classes:
    try:
        sig = inspect.signature(cls)
        doc = (cls.__doc__ or "").split('\n')[0] if cls.__doc__ else "No doc"
        print(f"{name}{sig}: {doc}")
    except:
        print(f"{name}: [signature unavailable]")

print("\n=== FUNCTIONS ===")
for name, func in functions:
    try:
        sig = inspect.signature(func)
        doc = (func.__doc__ or "").split('\n')[0] if func.__doc__ else "No doc"
        print(f"{name}{sig}: {doc}")
    except:
        print(f"{name}: [signature unavailable]")

print("\n=== OTHER ===")
for name, obj in other[:10]:  # Limit to first 10
    print(f"{name}: {type(obj).__name__}")