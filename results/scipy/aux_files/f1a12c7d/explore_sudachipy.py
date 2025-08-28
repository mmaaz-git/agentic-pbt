#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy
import sudachipy.dictionary
import inspect

print("=== sudachipy.dictionary attributes ===")
print(dir(sudachipy.dictionary))

print("\n=== sudachipy.dictionary module info ===")
print(f"Module file: {sudachipy.dictionary.__file__}")
print(f"Module doc: {sudachipy.dictionary.__doc__}")

print("\n=== Classes and functions in sudachipy.dictionary ===")
members = inspect.getmembers(sudachipy.dictionary)
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj)}")