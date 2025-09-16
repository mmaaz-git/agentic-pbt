#!/usr/bin/env python3
"""Minimal reproduction for integer validator bug."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

from troposphere.validators import integer

# Bug: integer validator accepts non-integer floats
print("Testing integer(0.5)...")
result = integer(0.5)
print(f"Result: {result}")
print(f"Type: {type(result)}")
print(f"int(result): {int(result)}")

print("\nTesting integer(3.14)...")
result = integer(3.14)
print(f"Result: {result}")
print(f"Type: {type(result)}")
print(f"int(result): {int(result)}")

# These should raise ValueError as they are not valid integers