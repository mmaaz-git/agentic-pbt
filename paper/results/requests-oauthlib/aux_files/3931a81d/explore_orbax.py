#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint as ocp
import inspect
import types

# List public functions and classes
members = inspect.getmembers(ocp, lambda x: (inspect.isfunction(x) or inspect.isclass(x)) and not x.__name__.startswith('_'))
print("=== Public classes and functions in orbax.checkpoint ===")
for name, obj in members[:30]:  # First 30 items
    if inspect.isclass(obj):
        print(f'Class: {name}')
        # Get __init__ signature if available
        try:
            sig = inspect.signature(obj.__init__)
            print(f'  __init__ signature: {sig}')
        except:
            pass
    else:
        print(f'Function: {name}')
        try:
            sig = inspect.signature(obj)
            print(f'  Signature: {sig}')
        except:
            pass

print("\n=== Key classes to focus on ===")
# Look at some key classes more closely
key_classes = ['CheckpointManager', 'Checkpointer', 'PyTreeCheckpointer', 'StandardCheckpointer']
for class_name in key_classes:
    if hasattr(ocp, class_name):
        cls = getattr(ocp, class_name)
        print(f"\n{class_name}:")
        if cls.__doc__:
            print(f"  Docstring (first 200 chars): {cls.__doc__[:200]}...")