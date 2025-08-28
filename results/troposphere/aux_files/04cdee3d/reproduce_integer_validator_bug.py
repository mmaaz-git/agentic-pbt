"""Minimal reproduction of the integer validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Bug: integer() validator raises OverflowError instead of ValueError for infinity
try:
    validators.integer(float('inf'))
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")
    print("Expected: ValueError with message 'inf is not a valid integer'")