#!/usr/bin/env python3
"""Test more edge cases for integer validator"""
from troposphere.validators import integer
import math

# Test NaN
print("Testing NaN:")
try:
    result = integer(float('nan'))
    print(f"Unexpectedly succeeded: {result}")
except ValueError as e:
    print(f"Raised ValueError as expected: {e}")
except Exception as e:
    print(f"Raised unexpected exception {type(e).__name__}: {e}")

# Test very large float
print("\nTesting very large float:")
try:
    result = integer(1e308)
    print(f"Result: {result}")
    int_val = int(result)
    print(f"Converted to int: {int_val}")
except ValueError as e:
    print(f"Raised ValueError: {e}")
except OverflowError as e:
    print(f"BUG: Raised OverflowError instead of ValueError: {e}")
except Exception as e:
    print(f"Raised unexpected exception {type(e).__name__}: {e}")