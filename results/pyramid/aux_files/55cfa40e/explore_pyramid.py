#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.interfaces as pi

# Get all public interfaces (not starting with underscore)
members = inspect.getmembers(pi, lambda x: inspect.isclass(x) and hasattr(x, '__name__'))
interfaces = [(name, obj) for name, obj in members if name.startswith('I') and not name.startswith('_')]

print(f"Found {len(interfaces)} interfaces in pyramid.interfaces:")
for name, obj in interfaces[:10]:  # Show first 10
    print(f"  - {name}")
    # Check if it has any concrete methods (not just interface definitions)
    if hasattr(obj, '__dict__'):
        methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m, None))]
        if methods:
            print(f"    Methods: {methods[:3]}...")
            
# Also check for any concrete classes or functions
functions = inspect.getmembers(pi, inspect.isfunction)
if functions:
    print(f"\nFound {len(functions)} functions:")
    for name, _ in functions[:5]:
        print(f"  - {name}")

# Check for any concrete implementations
concrete_classes = [(name, obj) for name, obj in members if not name.startswith('I') and not name.startswith('_')]
if concrete_classes:
    print(f"\nFound {len(concrete_classes)} concrete classes/objects:")
    for name, _ in concrete_classes[:5]:
        print(f"  - {name}")