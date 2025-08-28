#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

import inspect
import log_request_id.middleware as middleware

# Get all members of the module
members = inspect.getmembers(middleware)
print('Module members:')
for name, obj in members:
    if not name.startswith('_'):
        print(f'  {name}: {type(obj).__name__}')

# Get details about RequestIDMiddleware
cls = middleware.RequestIDMiddleware
print('\nRequestIDMiddleware methods:')
for name, method in inspect.getmembers(cls):
    if not name.startswith('_') and callable(method):
        try:
            sig = inspect.signature(method)
            print(f'  {name}{sig}')
        except:
            print(f'  {name}')

# Get method source code for key methods
print('\n_generate_id source:')
print(inspect.getsource(cls._generate_id))

print('\n_get_request_id source:')
print(inspect.getsource(cls._get_request_id))