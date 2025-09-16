#!/usr/bin/env python3
"""Minimal reproductions of bugs found in trino.types."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from datetime import time
from decimal import Decimal
from trino.types import Time, NamedRowTuple

print("Bug 1: NamedRowTuple shadows tuple methods")
print("-" * 40)
try:
    row = NamedRowTuple([1, 2, 3], ["count", "field2", "field3"], ["int", "int", "int"])
    print(f"row.count = {row.count}")  # Returns 1 (the value)
    print(f"Calling row.count(1)...")
    result = row.count(1)  # Should count occurrences of 1, but crashes
    print(f"Result: {result}")
except TypeError as e:
    print(f"ERROR: {e}")
    print("The 'count' field shadows the tuple's count() method!")

print("\n" + "=" * 60 + "\n")

print("Bug 2: NaN handling in round_to() crashes")
print("-" * 40)
try:
    time_obj = Time(time(12, 0, 0), Decimal('NaN'))
    print("Created Time object with NaN fractional seconds")
    print("Calling round_to(3)...")
    rounded = time_obj.round_to(3)
    print(f"Success: {rounded}")
except TypeError as e:
    print(f"ERROR: {e}")
    print("The round_to() method doesn't handle NaN properly!")

print("\n" + "=" * 60 + "\n")

print("Bug 3: Negative precision causes KeyError")
print("-" * 40)
try:
    time_obj = Time(time(12, 0, 0), Decimal('0.123456'))
    print("Created Time object with fractional seconds")
    print("Calling round_to(-1)...")
    rounded = time_obj.round_to(-1)
    print(f"Success: {rounded}")
except KeyError as e:
    print(f"ERROR: KeyError {e}")
    print("The round_to() method doesn't handle negative precision!")