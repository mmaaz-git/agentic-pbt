#!/usr/bin/env python3
"""Minimal reproduction for boolean validator bug."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

from troposphere.validators import boolean

# Bug: boolean validator accepts float 0.0 which is not in the documented accepted values
print("Testing boolean(0.0)...")
result = boolean(0.0)
print(f"Result: {result}")
print(f"Type: {type(result)}")

# This should have raised ValueError according to the function logic
# The function only accepts: True, 1, "1", "true", "True", False, 0, "0", "false", "False"
# Float 0.0 is not in this list

print("\nTesting boolean(1.0)...")
result = boolean(1.0)
print(f"Result: {result}")
print(f"Type: {type(result)}")