#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import inspect
import srsly

print("=== srsly Module Analysis ===")
print(f"Module file: {srsly.__file__}")
print(f"Version: {srsly.__version__ if hasattr(srsly, '__version__') else 'unknown'}")
print()

print("=== Public Functions and Classes ===")
members = inspect.getmembers(srsly)
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"{name}: {obj_type}")
        if callable(obj) and hasattr(obj, '__doc__') and obj.__doc__:
            doc_lines = obj.__doc__.strip().split('\n')
            first_line = doc_lines[0] if doc_lines else ''
            print(f"  Doc: {first_line[:100]}")
print()

print("=== Main API Functions ===")
main_functions = ['json_dumps', 'json_loads', 'msgpack_dumps', 'msgpack_loads', 
                  'pickle_dumps', 'pickle_loads', 'yaml_dumps', 'yaml_loads',
                  'read_json', 'write_json', 'read_jsonl', 'write_jsonl',
                  'read_msgpack', 'write_msgpack', 'read_pickle', 'write_pickle',
                  'read_yaml', 'write_yaml']

for func_name in main_functions:
    if hasattr(srsly, func_name):
        func = getattr(srsly, func_name)
        print(f"\n{func_name}:")
        try:
            sig = inspect.signature(func)
            print(f"  Signature: {sig}")
        except:
            print(f"  Signature: Could not get signature")
        if hasattr(func, '__doc__') and func.__doc__:
            doc_lines = func.__doc__.strip().split('\n')
            for line in doc_lines[:3]:
                print(f"  {line}")