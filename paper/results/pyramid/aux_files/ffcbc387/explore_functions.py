#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import inspect
from pyramid import settings, encode, util

# Functions to examine in detail
functions_to_examine = [
    (settings, 'asbool'),
    (settings, 'aslist'),
    (settings, 'aslist_cronly'),
    (encode, 'url_quote'),
    (encode, 'quote_plus'),
    (encode, 'urlencode'),
    (util, 'as_sorted_tuple'),
]

for module, func_name in functions_to_examine:
    try:
        func = getattr(module, func_name)
        print(f"\n{'='*60}")
        print(f"Function: {module.__name__}.{func_name}")
        print('='*60)
        
        # Get signature
        sig = inspect.signature(func)
        print(f"Signature: {func_name}{sig}")
        
        # Get docstring
        doc = func.__doc__
        if doc:
            print(f"\nDocstring:")
            print(doc[:500] if len(doc) > 500 else doc)
        
        # Get source code
        try:
            source = inspect.getsource(func)
            print(f"\nSource (first 30 lines):")
            lines = source.split('\n')[:30]
            for i, line in enumerate(lines, 1):
                print(f"  {i:3}: {line}")
        except:
            print("Source not available")
            
    except Exception as e:
        print(f"Error examining {func_name}: {e}")