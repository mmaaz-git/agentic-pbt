#!/usr/bin/env python3
"""
Minimal reproduction of make_recoder behavior with invalid inputs.

make_recoder is designed to work with Python code objects (functions, classes, modules)
but raises ResolutionError when given other types.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.recode import make_recoder

# This will raise ResolutionError
try:
    result = make_recoder(None)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e.__class__.__name__}: {e}")

# Also fails with other non-code objects
try:
    result = make_recoder("not a function")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e.__class__.__name__}: {e}")

# Expected usage - with an actual function
def example_function():
    return 42

try:
    result = make_recoder(example_function)
    print(f"Result for function: {result}")
except Exception as e:
    print(f"Error for function: {e.__class__.__name__}: {e}")