#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.athena
import inspect

print('Module imported successfully')
print('Module file:', troposphere.athena.__file__)
print('\nPublic members:')
members = inspect.getmembers(troposphere.athena, lambda x: not inspect.ismodule(x))
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")