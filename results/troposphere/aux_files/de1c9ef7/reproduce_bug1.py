#!/usr/bin/env python3
"""Reproduce boolean validator bug with float input"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test: boolean validator should reject float 0.0 but doesn't
print("Testing boolean(0.0)...")
try:
    result = boolean(0.0)
    print(f"BUG: boolean(0.0) returned {result} instead of raising ValueError")
    print(f"Result type: {type(result)}")
except ValueError as e:
    print(f"OK: Raised ValueError as expected: {e}")

# Test similar floats
print("\nTesting boolean(1.0)...")
try:
    result = boolean(1.0)
    print(f"BUG: boolean(1.0) returned {result} instead of raising ValueError")
except ValueError:
    print("OK: Raised ValueError as expected")

print("\nTesting boolean(0.5)...")
try:
    result = boolean(0.5)
    print(f"BUG: boolean(0.5) returned {result} instead of raising ValueError")
except ValueError:
    print("OK: Raised ValueError as expected")