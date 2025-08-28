#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import InquirerPy.containers as target
import inspect

print('Module file:', target.__file__)
print('\nPublic members:')
for name, obj in inspect.getmembers(target):
    if not name.startswith('_'):
        print(f'  {name}: {type(obj).__name__}')

# Get more details on classes
print('\nClasses with their methods:')
for name, obj in inspect.getmembers(target):
    if not name.startswith('_') and inspect.isclass(obj):
        print(f'\n{name}:')
        print(f'  Docstring: {obj.__doc__}')
        print('  Methods:')
        for method_name, method in inspect.getmembers(obj):
            if not method_name.startswith('_') and callable(method):
                sig = None
                try:
                    sig = inspect.signature(method)
                except:
                    pass
                print(f'    {method_name}{sig if sig else "()"}')