#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

# Let's find how these functions are used in the codebase
pyramid_dir = '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages/pyramid'

# Functions to search for
functions_to_find = [
    'asbool',
    'aslist',
    'urlencode',
    'as_sorted_tuple'
]

import glob

# Search for usage patterns in pyramid code
for func_name in functions_to_find:
    print(f"\n{'='*60}")
    print(f"Searching for usage of: {func_name}")
    print('='*60)
    
    # Get all .py files
    py_files = glob.glob(os.path.join(pyramid_dir, '**/*.py'), recursive=True)
    
    count = 0
    for py_file in py_files:
        with open(py_file, 'r') as f:
            try:
                content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if func_name in line and not line.strip().startswith('#'):
                        # Skip definition lines
                        if f'def {func_name}' not in line:
                            count += 1
                            if count <= 3:  # Show first 3 examples
                                rel_path = os.path.relpath(py_file, pyramid_dir)
                                print(f"  {rel_path}:{i}: {line.strip()}")
            except:
                pass
    
    if count > 3:
        print(f"  ... and {count - 3} more occurrences")