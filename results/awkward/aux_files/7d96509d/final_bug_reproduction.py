#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

print("=== BUG: ak.mask fails on empty arrays created from Python lists ===\n")

# Demonstrate the bug
print("Minimal reproduction:")
print("-" * 40)

# Create empty arrays
empty_data = ak.Array([])
empty_mask = ak.Array([])  # This will have type '0 * unknown'

print(f"empty_data = ak.Array([])")
print(f"empty_mask = ak.Array([])")
print(f"empty_data.type = {empty_data.type}")
print(f"empty_mask.type = {empty_mask.type}")
print()

# Try to mask - this should logically work but fails
print("Attempting: ak.mask(empty_data, empty_mask, valid_when=False)")
try:
    result = ak.mask(empty_data, empty_mask, valid_when=False)
    print(f"Result: {result}")
except ValueError as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Expected behavior:")
print("-" * 40)

# Show that it works with properly typed empty boolean array
empty_bool_mask = ak.Array(np.array([], dtype=bool))
print(f"empty_bool_mask = ak.Array(np.array([], dtype=bool))")
print(f"empty_bool_mask.type = {empty_bool_mask.type}")
print()

print("Attempting: ak.mask(empty_data, empty_bool_mask, valid_when=False)")
result = ak.mask(empty_data, empty_bool_mask, valid_when=False)
print(f"Result: {result} (SUCCESS)")

print("\n" + "=" * 60)
print("Why this is a bug:")
print("-" * 40)
print("1. The operation is logically valid: masking 0 elements with 0 masks")
print("2. Both arrays have the same length (0), satisfying the documented requirement")
print("3. The function rejects it solely due to type checking, not logical invalidity")
print("4. Empty arrays from Python lists get type '0 * unknown' → interpreted as float64")
print("5. This breaks the principle of least surprise for edge cases")