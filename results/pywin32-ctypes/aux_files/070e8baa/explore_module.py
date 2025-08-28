#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

import win32ctypes.core
import inspect
import os

print("Successfully imported win32ctypes.core")
print(f"Module file: {win32ctypes.core.__file__}")
print(f"Module dir: {os.path.dirname(win32ctypes.core.__file__)}")

# Get all members of the module
members = inspect.getmembers(win32ctypes.core)
print("\nModule members:")
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj)}")