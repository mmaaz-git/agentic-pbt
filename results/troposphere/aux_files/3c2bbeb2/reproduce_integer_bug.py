"""Minimal reproduction of integer validator bug with infinity"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test with float infinity
import math

test_values = [
    float('inf'),
    float('-inf'),
    math.inf,
    -math.inf,
    42,  # Regular integer
    "42",  # String integer
    3.14,  # Regular float
]

for value in test_values:
    print(f"\nTesting value: {value!r} (type: {type(value).__name__})")
    try:
        result = validators.integer(value)
        print(f"  validators.integer() returned: {result}")
    except ValueError as e:
        print(f"  ValueError: {e}")
    except OverflowError as e:
        print(f"  OverflowError: {e}")
    except Exception as e:
        print(f"  Unexpected error ({type(e).__name__}): {e}")
    
    # Also test what int() does directly
    try:
        int_result = int(value)
        print(f"  int() returned: {int_result}")
    except Exception as e:
        print(f"  int() raised {type(e).__name__}: {e}")