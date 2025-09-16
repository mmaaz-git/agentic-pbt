#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.auditmanager as am
import inspect

print("=== Module file location ===")
print(am.__file__)
print()

print("=== All members of the module ===")
members = inspect.getmembers(am)
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")

print("\n=== Classes in the module ===")
classes = [name for name, obj in members if inspect.isclass(obj) and not name.startswith('_')]
print(classes)

print("\n=== Functions in the module ===")
functions = [name for name, obj in members if inspect.isfunction(obj) and not name.startswith('_')]
print(functions)