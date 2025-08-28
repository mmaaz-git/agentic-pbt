#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import pyct.build
import inspect
import os

# Get module info
print('Module location:', pyct.build.__file__)
print('Module members:')
for name, obj in inspect.getmembers(pyct.build):
    if not name.startswith('_'):
        print(f'  {name}: {type(obj).__name__}')

# Get function signatures and docs
print('\nFunction details:')
for func_name in ['examples', 'get_setup_version']:
    if hasattr(pyct.build, func_name):
        func = getattr(pyct.build, func_name)
        print(f'\n{func_name}:')
        print('  Signature:', inspect.signature(func))
        if func.__doc__:
            print('  Docstring:', func.__doc__.strip())

# Check if there are tests for this module
test_path = os.path.join(os.path.dirname(pyct.build.__file__), 'tests')
if os.path.exists(test_path):
    print('\nTests directory found at:', test_path)
    test_files = [f for f in os.listdir(test_path) if f.endswith('.py')]
    print('Test files:', test_files)