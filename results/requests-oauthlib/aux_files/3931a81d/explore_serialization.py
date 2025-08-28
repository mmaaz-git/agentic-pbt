#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint as ocp
import orbax.checkpoint.serialization as serialization
import orbax.checkpoint.transform_utils as transform_utils
import orbax.checkpoint.msgpack_utils as msgpack_utils
import inspect

# Look at serialization module
print("=== Serialization module functions ===")
for name in dir(serialization):
    if not name.startswith('_'):
        obj = getattr(serialization, name)
        if callable(obj):
            print(f"{name}: {type(obj)}")

# Look at transform_utils
print("\n=== Transform utils functions ===")
for name in dir(transform_utils):
    if not name.startswith('_'):
        obj = getattr(transform_utils, name)
        if callable(obj) and not inspect.isclass(obj):
            print(f"{name}: {type(obj)}")
            if obj.__doc__:
                print(f"  Doc: {obj.__doc__[:150]}...")

# Look at msgpack utils
print("\n=== Msgpack utils functions ===")
for name in dir(msgpack_utils):
    if not name.startswith('_'):
        obj = getattr(msgpack_utils, name)
        if callable(obj) and not inspect.isclass(obj):
            print(f"{name}: {type(obj)}")
            if obj.__doc__:
                print(f"  Doc: {obj.__doc__[:150]}...")

# Check tree module functions
import orbax.checkpoint.tree as tree_module
print("\n=== Tree module functions ===")
for name in dir(tree_module):
    if not name.startswith('_'):
        obj = getattr(tree_module, name)
        if callable(obj) and not inspect.isclass(obj):
            print(f"{name}: {type(obj)}")
            if obj.__doc__:
                print(f"  Doc: {obj.__doc__[:150]}...")