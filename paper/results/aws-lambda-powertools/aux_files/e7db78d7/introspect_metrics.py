#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import inspect
import aws_lambda_powertools.metrics as metrics

# Get all public members
members = inspect.getmembers(metrics, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else True)

print("Public members of aws_lambda_powertools.metrics:")
print("=" * 60)

for name, obj in members:
    if name.startswith('_'):
        continue
    obj_type = type(obj).__name__
    print(f"{name}: {obj_type}")
    
print("\n" + "=" * 60)
print("Key classes and functions for deeper analysis:")
print("=" * 60)

# Focus on main classes and functions
for name, obj in members:
    if name.startswith('_'):
        continue
    if inspect.isclass(obj) or inspect.isfunction(obj):
        print(f"\n{name} ({type(obj).__name__}):")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Docstring preview: {obj.__doc__[:200]}...")
        if inspect.isclass(obj):
            # Show public methods
            methods = [m for m in dir(obj) if not m.startswith('_')]
            print(f"  Public methods: {methods[:10]}")  # Show first 10