#!/usr/bin/env python3
"""Minimal reproductions of discovered bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.mwaa as mwaa

print("Bug 1: Integer validator crashes on infinity")
print("=" * 50)
try:
    result = integer(float('inf'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except OverflowError as e:
    print(f"OverflowError (BUG!): {e}")

print("\nBug 2: Environment accepts empty title")
print("=" * 50)
try:
    env = mwaa.Environment("")
    print(f"Created environment with empty title: {env.title}")
    print("BUG: Should have raised ValueError for empty title")
except ValueError as e:
    print(f"ValueError (expected): {e}")