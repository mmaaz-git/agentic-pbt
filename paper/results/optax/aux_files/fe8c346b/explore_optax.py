#!/usr/bin/env python3
"""Explore the optax module structure to find key functions and classes."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import optax
import inspect
from collections import defaultdict

def explore_module(module, prefix=""):
    """Explore a module's structure and categorize its members."""
    categories = defaultdict(list)
    
    for name, obj in inspect.getmembers(module):
        if name.startswith('_'):
            continue
        
        if inspect.isfunction(obj):
            categories['functions'].append((name, obj))
        elif inspect.isclass(obj):
            categories['classes'].append((name, obj))
        elif inspect.ismodule(obj) and obj.__name__.startswith('optax'):
            categories['submodules'].append((name, obj))
        else:
            categories['other'].append((name, type(obj).__name__))
    
    return categories

# Explore main optax module
print("=== OPTAX MODULE STRUCTURE ===\n")
categories = explore_module(optax)

print(f"Found {len(categories['functions'])} functions:")
for name, func in categories['functions'][:10]:  # Show first 10
    try:
        sig = inspect.signature(func)
        doc = func.__doc__.split('\n')[0] if func.__doc__ else "No docstring"
        print(f"  - {name}{sig}: {doc[:60]}...")
    except:
        print(f"  - {name}: (signature unavailable)")

print(f"\nFound {len(categories['classes'])} classes")

# Focus on key transform functions
print("\n=== KEY TRANSFORMATION FUNCTIONS ===")
transform_funcs = [
    'scale', 'scale_by_adam', 'scale_by_rms', 'clip', 'clip_by_global_norm',
    'apply_updates', 'chain', 'sgd', 'adam', 'adamw'
]

for func_name in transform_funcs:
    if hasattr(optax, func_name):
        func = getattr(optax, func_name)
        if callable(func):
            print(f"\n{func_name}:")
            try:
                sig = inspect.signature(func)
                print(f"  Signature: {sig}")
                if func.__doc__:
                    doc_lines = func.__doc__.split('\n')
                    print(f"  Doc: {doc_lines[0][:100]}")
            except:
                print(f"  (Details unavailable)")

# Look at the schedules module for learning rate schedules
print("\n=== SCHEDULES MODULE ===")
if hasattr(optax, 'schedules'):
    schedule_categories = explore_module(optax.schedules)
    print(f"Found {len(schedule_categories['functions'])} schedule functions:")
    for name, func in schedule_categories['functions'][:5]:
        print(f"  - {name}")

# Look at losses module
print("\n=== LOSSES MODULE ===")
if hasattr(optax, 'losses'):
    losses_categories = explore_module(optax.losses)
    print(f"Found {len(losses_categories['functions'])} loss functions:")
    for name, func in losses_categories['functions'][:5]:
        print(f"  - {name}")

# Look at numerics utilities
print("\n=== NUMERIC UTILITIES ===")
numerics_funcs = ['safe_norm', 'safe_root_mean_squares', 'safe_increment', 'global_norm']
for func_name in numerics_funcs:
    if hasattr(optax, func_name):
        func = getattr(optax, func_name)
        if callable(func):
            print(f"  - {func_name}: {func.__doc__.split(chr(10))[0] if func.__doc__ else 'No doc'}")