#!/usr/bin/env python3
"""Minimal reproduction of the FlagDecorator bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiogram_env/lib/python3.13/site-packages')

from aiogram.dispatcher.flags import FlagDecorator, Flag

# Create a flag decorator
flag = Flag("test_flag", True)
decorator = FlagDecorator(flag)

# This should raise ValueError but doesn't when value=0
def dummy_func():
    pass

# Bug: when value=0 (or any falsy value), the check passes incorrectly
try:
    result = decorator(0, some_kwarg=123)
    print(f"Bug confirmed! No ValueError raised when value=0 and kwargs provided")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError correctly raised: {e}")

# Also test with other falsy values
print("\nTesting other falsy values:")
for falsy_value in [False, "", [], {}, None]:
    try:
        result = decorator(falsy_value, kwarg=1)
        print(f"  {falsy_value!r}: No error (BUG)")
    except ValueError:
        print(f"  {falsy_value!r}: ValueError raised (correct)")