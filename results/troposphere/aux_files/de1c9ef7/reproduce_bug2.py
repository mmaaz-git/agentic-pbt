#!/usr/bin/env python3
"""Reproduce integer validator bug with float input"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Test: integer validator should reject or properly handle floats
print("Testing integer(0.0)...")
try:
    result = integer(0.0)
    print(f"Result: {result}")
    print(f"Result type: {type(result)}")
    print(f"int(result): {int(result)}")
except (ValueError, TypeError) as e:
    print(f"Raised error: {e}")

print("\nTesting integer(1.5)...")
try:
    result = integer(1.5)
    print(f"Result: {result}")
    print(f"Result type: {type(result)}")
except (ValueError, TypeError) as e:
    print(f"Raised error: {e}")

print("\nTesting integer(123.0)...")
try:
    result = integer(123.0)
    print(f"Result: {result}")
    print(f"Result type: {type(result)}")
except (ValueError, TypeError) as e:
    print(f"Raised error: {e}")