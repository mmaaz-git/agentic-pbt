#!/usr/bin/env python3
"""
Comprehensive test of the boolean validator with various invalid inputs.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test various invalid values
invalid_values = [
    -1,
    2,
    1.5,
    "yes",
    "no",
    "TRUE",  # uppercase variations
    "FALSE",
    [],
    {},
    None,
    "1.0",
    "0.0",
]

print("Testing invalid values for boolean validator:")
print("=" * 50)

for value in invalid_values:
    try:
        result = boolean(value)
        print(f"boolean({repr(value)}) = {result} (UNEXPECTED: should have raised ValueError)")
    except ValueError as e:
        msg = str(e)
        if msg:
            print(f"boolean({repr(value)}) raised ValueError with message: '{msg}'")
        else:
            print(f"boolean({repr(value)}) raised ValueError with NO MESSAGE (BUG!)")
    except Exception as e:
        print(f"boolean({repr(value)}) raised {type(e).__name__}: {e}")