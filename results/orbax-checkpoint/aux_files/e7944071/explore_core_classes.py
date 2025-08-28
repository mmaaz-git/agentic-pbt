#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint
import inspect

# Core classes to explore
core_classes = [
    orbax.checkpoint.Checkpointer,
    orbax.checkpoint.CheckpointManager,
    orbax.checkpoint.PyTreeCheckpointHandler,
    orbax.checkpoint.ArrayCheckpointHandler,
    orbax.checkpoint.StandardCheckpointHandler,
]

for cls in core_classes:
    print(f"\n{'='*60}")
    print(f"Class: {cls.__name__}")
    print(f"{'='*60}")
    
    # Get docstring
    if cls.__doc__:
        doc_lines = cls.__doc__.strip().split('\n')
        print("Docstring (first 5 lines):")
        for line in doc_lines[:5]:
            print(f"  {line}")
    
    # Get public methods
    methods = []
    for name, method in inspect.getmembers(cls):
        if not name.startswith('_') and callable(method):
            methods.append(name)
    
    print(f"\nPublic methods ({len(methods)}):")
    for m in methods[:10]:  # Show first 10
        print(f"  - {m}")
    
    # Get source file
    try:
        source_file = inspect.getfile(cls)
        print(f"\nSource file: {source_file}")
    except:
        print("\nCould not get source file")