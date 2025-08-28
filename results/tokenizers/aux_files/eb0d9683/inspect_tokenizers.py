#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import inspect
import tokenizers
from tokenizers import tokenizers as tokenizers_module

print("=== tokenizers module location ===")
print(f"tokenizers module file: {tokenizers.__file__}")

print("\n=== tokenizers.tokenizers module inspection ===")
print(f"Type: {type(tokenizers_module)}")

print("\n=== Public members in tokenizers.tokenizers ===")
members = inspect.getmembers(tokenizers_module)
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj)}")

print("\n=== Classes in tokenizers.tokenizers ===")
classes = [name for name, obj in members if inspect.isclass(obj) and not name.startswith('_')]
print(classes)

print("\n=== Functions in tokenizers.tokenizers ===")
functions = [name for name, obj in members if inspect.isfunction(obj) and not name.startswith('_')]
print(functions)