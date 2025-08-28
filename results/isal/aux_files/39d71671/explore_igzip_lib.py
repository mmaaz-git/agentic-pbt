#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_lib
import inspect

print('Module file:', isal.igzip_lib.__file__)
print()

members = inspect.getmembers(isal.igzip_lib)
print('Public members:')
for name, obj in members:
    if not name.startswith('_'):
        print(f'  {name}: {type(obj).__name__}')
print()

print('All members (including private):')
for name, obj in members:
    print(f'  {name}: {type(obj).__name__}')