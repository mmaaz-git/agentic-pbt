#!/usr/bin/env python3

import sys
import types

# Mock cfn_flip
sys.modules['cfn_flip'] = types.ModuleType('cfn_flip')

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/worker_/1/troposphere-4.9.3')

from troposphere.validators import integer

# Test the bug with infinity
print("Testing integer validator with float('inf')...")
try:
    result = integer(float('inf'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except OverflowError as e:
    print(f"OverflowError (unexpected!): {e}")
    print("BUG FOUND: integer() raises OverflowError instead of ValueError for infinity")

print("\nTesting integer validator with float('-inf')...")
try:
    result = integer(float('-inf'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except OverflowError as e:
    print(f"OverflowError (unexpected!): {e}")
    print("BUG FOUND: integer() raises OverflowError instead of ValueError for -infinity")

print("\nTesting integer validator with float('nan')...")
try:
    result = integer(float('nan'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except Exception as e:
    print(f"Other exception: {type(e).__name__}: {e}")

# The issue is in the integer() function implementation:
# It tries int(x) and catches ValueError and TypeError, but not OverflowError
print("\n--- Analysis ---")
print("The integer() validator function has a bug:")
print("1. It calls int(x) to validate the input")
print("2. It catches ValueError and TypeError")
print("3. But it doesn't catch OverflowError")
print("4. When given float('inf') or float('-inf'), int() raises OverflowError")
print("5. This causes an unhandled exception instead of the expected ValueError")