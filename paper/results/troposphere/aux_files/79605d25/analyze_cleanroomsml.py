#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cleanroomsml as crml
import inspect

# Get all public classes and functions
print("=== Classes in troposphere.cleanroomsml ===")
members = inspect.getmembers(crml, inspect.isclass)
for name, cls in members:
    if not name.startswith('_'):
        print(f"\n{name}:")
        print(f"  Base classes: {[b.__name__ for b in cls.__bases__]}")
        if hasattr(cls, 'props'):
            print(f"  Properties:")
            for prop_name, prop_info in cls.props.items():
                prop_type, required = prop_info
                print(f"    - {prop_name}: {prop_type} (required={required})")
        
        # Get methods
        methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
        if methods:
            print(f"  Methods: {methods}")

# Check for any functions
funcs = inspect.getmembers(crml, inspect.isfunction)
if funcs:
    print("\n=== Functions ===")
    for name, func in funcs:
        if not name.startswith('_'):
            print(f"{name}: {inspect.signature(func)}")