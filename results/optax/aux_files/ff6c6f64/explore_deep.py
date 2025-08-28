#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import inspect
import optax
from optax import schedules, tree

print("=== Looking for testable functions ===\n")

# Check schedules module (likely to have mathematical properties)
print("=== Schedule Functions ===")
schedule_members = inspect.getmembers(schedules, inspect.isfunction)
for name, func in schedule_members[:10]:
    if not name.startswith('_'):
        try:
            sig = inspect.signature(func)
            doc = func.__doc__
            if doc:
                doc_first_line = doc.split('\n')[0][:80]
            else:
                doc_first_line = "No documentation"
            print(f"{name}{sig}")
            print(f"  Doc: {doc_first_line}\n")
        except:
            pass

# Check tree module (likely to have invariants)
print("\n=== Tree Functions ===")
tree_members = inspect.getmembers(tree, inspect.isfunction)
for name, func in tree_members[:10]:
    if not name.startswith('_'):
        try:
            sig = inspect.signature(func)
            doc = func.__doc__
            if doc:
                doc_first_line = doc.split('\n')[0][:80]
            else:
                doc_first_line = "No documentation"
            print(f"{name}{sig}")
            print(f"  Doc: {doc_first_line}\n")
        except:
            pass

# Look for simple math functions in main module
print("\n=== Math/Utility Functions in Main Module ===")
interesting_funcs = ['clip', 'clip_by_global_norm', 'scale', 'scale_by_adam', 
                    'scale_by_stddev', 'add_decayed_weights', 'apply_every',
                    'zero_nans', 'identity', 'stateless']

for name in interesting_funcs:
    if hasattr(optax, name):
        func = getattr(optax, name)
        if callable(func):
            try:
                sig = inspect.signature(func)
                doc = func.__doc__
                if doc:
                    doc_first_line = doc.split('\n')[0][:80]
                else:
                    doc_first_line = "No documentation"
                print(f"{name}{sig}")
                print(f"  Doc: {doc_first_line}\n")
            except:
                pass