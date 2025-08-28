#!/usr/bin/env python3
"""Minimal reproduction of integer validator bug with infinity"""
from troposphere.validators import integer

# This should raise ValueError but instead raises OverflowError
try:
    result = integer(float('inf'))
    print(f"Unexpectedly succeeded: {result}")
except ValueError as e:
    print(f"Raised ValueError as expected: {e}")
except OverflowError as e:
    print(f"BUG: Raised OverflowError instead of ValueError: {e}")

# Same issue with negative infinity
try:
    result = integer(float('-inf'))
    print(f"Unexpectedly succeeded: {result}")
except ValueError as e:
    print(f"Raised ValueError as expected: {e}")
except OverflowError as e:
    print(f"BUG: Raised OverflowError instead of ValueError: {e}")