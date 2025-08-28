#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import inspect
import optax
from optax import tree

# Functions to inspect
funcs_to_inspect = ['add', 'add_scale', 'clip', 'div', 'full_like', 'cast', 'cast_like']

for func_name in funcs_to_inspect:
    func = getattr(tree, func_name)
    print(f"=== {func_name} ===")
    print(f"Signature: {inspect.signature(func)}")
    print(f"Docstring:\n{func.__doc__}\n")
    
    try:
        source_file = inspect.getfile(func)
        print(f"Source file: {source_file}")
    except:
        pass
    
    print("-" * 40)

# Also check schedules for mathematical properties
print("\n\n=== Schedule Functions for Testing ===")
schedule_funcs = ['constant_schedule', 'linear_schedule', 'exponential_decay']

for func_name in schedule_funcs:
    func = getattr(optax.schedules, func_name)
    print(f"=== {func_name} ===")
    print(f"Signature: {inspect.signature(func)}")
    print(f"Docstring:\n{func.__doc__}\n")
    print("-" * 40)