#!/usr/bin/env python3
"""Test more edge cases for the discovered bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.mwaa as mwaa
import math

print("Testing integer validator with special float values:")
print("=" * 50)

test_values = [
    float('inf'),
    float('-inf'),
    float('nan'),
    1e308,  # Very large but finite
    -1e308
]

for val in test_values:
    try:
        result = integer(val)
        print(f"{val}: Success -> {result}")
    except ValueError as e:
        print(f"{val}: ValueError (expected) -> {e}")
    except OverflowError as e:
        print(f"{val}: OverflowError (BUG!) -> {e}")
    except Exception as e:
        print(f"{val}: {type(e).__name__} -> {e}")

print("\nTesting Environment title validation:")
print("=" * 50)

test_titles = [
    "",  # Empty
    None,  # None
    " ",  # Space
    "Valid123",  # Valid
    "test-name",  # With hyphen
    "test_name",  # With underscore
    "123test",  # Starting with number
    "test name",  # With space
]

for title in test_titles:
    try:
        env = mwaa.Environment(title)
        print(f"'{title}': SUCCESS (title={env.title})")
    except (ValueError, TypeError) as e:
        print(f"'{title}': {type(e).__name__} -> {e}")