#!/usr/bin/env python3
"""Bug 1: Integer validator crashes on infinity"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# This should handle infinity gracefully but crashes instead
try:
    result = integer(float('inf'))
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("BUG: integer validator doesn't catch OverflowError for infinity")
except ValueError as e:
    print(f"ValueError (expected): {e}")