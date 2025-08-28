#!/usr/bin/env python3
"""Minimal reproduction of boolean validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test case found by Hypothesis
print("Testing validators.boolean(0.0)...")
result = validators.boolean(0.0)
print(f"Result: {result}")
print(f"Type: {type(result)}")

# Test with other float values
print("\nTesting validators.boolean(1.0)...")
result = validators.boolean(1.0)
print(f"Result: {result}")
print(f"Type: {type(result)}")

# Test with non-zero float
print("\nTesting validators.boolean(0.5)...")
try:
    result = validators.boolean(0.5)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
except ValueError as e:
    print(f"ValueError: {e}")

# Show the actual validator code
print("\n--- Boolean validator code ---")
import inspect
print(inspect.getsource(validators.boolean))