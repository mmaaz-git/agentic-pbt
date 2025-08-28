#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy.dictionary
import inspect

Dictionary = sudachipy.dictionary.Dictionary

print("=== Dictionary class info ===")
print(f"Dictionary class: {Dictionary}")
print(f"Dictionary docstring: {Dictionary.__doc__}")
print(f"Dictionary file: {inspect.getfile(Dictionary)}")

print("\n=== Dictionary class members ===")
members = inspect.getmembers(Dictionary)
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")
        if callable(obj) and hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Doc: {obj.__doc__[:200]}")

print("\n=== Dictionary instance methods (signature inspection) ===")
for name, obj in members:
    if not name.startswith('_') and callable(obj):
        try:
            sig = inspect.signature(obj)
            print(f"{name}{sig}")
        except Exception as e:
            print(f"{name}: Could not get signature - {e}")