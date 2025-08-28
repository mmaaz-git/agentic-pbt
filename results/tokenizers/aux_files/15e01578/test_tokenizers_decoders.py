#!/usr/bin/env /root/hypothesis-llm/envs/tokenizers_env/bin/python3

import inspect
import tokenizers.decoders

# Get all public functions/classes in the module
members = inspect.getmembers(tokenizers.decoders)

# Print module info
print(f"Module: {tokenizers.decoders}")
print(f"Module file: {tokenizers.decoders.__file__ if hasattr(tokenizers.decoders, '__file__') else 'N/A'}")
print(f"Module doc: {tokenizers.decoders.__doc__ or 'No documentation'}")
print()

# List all public members
print("Public members:")
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  - {name}: {obj_type}")