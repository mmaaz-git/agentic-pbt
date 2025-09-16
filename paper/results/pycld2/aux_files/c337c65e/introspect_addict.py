#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

import addict
import inspect

print('Module file:', addict.__file__)
print('Module doc:', addict.__doc__)
print()

members = inspect.getmembers(addict)
print('Public members:')
for name, obj in members:
    if not name.startswith('_'):
        print(f'  {name}: {type(obj).__name__}')