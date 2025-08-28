"""Minimal reproduction of integer validator bug with infinity"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Bug: integer validator doesn't handle infinity properly
print("Testing integer validator with float('inf')...")
try:
    result = integer(float('inf'))
    print(f"Unexpected success: {result}")
except ValueError as e:
    print(f"Expected ValueError: {e}")
except OverflowError as e:
    print(f"BUG - Got OverflowError instead of ValueError: {e}")

print("\nTesting integer validator with float('-inf')...")
try:
    result = integer(float('-inf'))
    print(f"Unexpected success: {result}")
except ValueError as e:
    print(f"Expected ValueError: {e}")
except OverflowError as e:
    print(f"BUG - Got OverflowError instead of ValueError: {e}")

print("\nExpected behavior with non-integer float...")
try:
    result = integer(3.14)
    print(f"Result: {result}")
except ValueError as e:
    print(f"Got expected ValueError: {e}")