#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib
import inspect
import os

print("Module imported successfully!")
print(f"Module file: {isal.isal_zlib.__file__}")
print(f"Module doc: {isal.isal_zlib.__doc__}")
print()

# Get all members
members = inspect.getmembers(isal.isal_zlib)
print("Module members:")
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj)}")