#!/usr/bin/env python3
import troposphere.ce
import inspect

print("Module found:", troposphere.ce)
print("Module file:", troposphere.ce.__file__)
print("\nPublic members:")
members = inspect.getmembers(troposphere.ce, lambda x: not inspect.ismodule(x))
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")