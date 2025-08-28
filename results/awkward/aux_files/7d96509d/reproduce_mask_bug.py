#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

# Minimal reproduction
print("Testing empty array mask issue:")

# Create an empty integer array
arr = ak.Array([])
print(f"arr = {arr}")
print(f"arr type = {arr.type}")

# Create an empty boolean mask
mask_list = []
mask = ak.Array(mask_list)
print(f"\nmask = {mask}")
print(f"mask type = {mask.type}")

# Try to apply the mask
try:
    masked = ak.mask(arr, mask, valid_when=False)
    print(f"Success: masked = {masked}")
except Exception as e:
    print(f"ERROR: {e}")

# Let's try with explicit boolean type
print("\n--- Trying with explicit boolean type ---")
mask_bool = ak.Array([], dtype="bool")
print(f"mask_bool = {mask_bool}")
print(f"mask_bool type = {mask_bool.type}")

try:
    masked = ak.mask(arr, mask_bool, valid_when=False)
    print(f"Success: masked = {masked}")
except Exception as e:
    print(f"ERROR: {e}")

# Also test with non-empty arrays
print("\n--- Testing with non-empty arrays ---")
arr2 = ak.Array([1, 2, 3])
mask2 = ak.Array([True, False, True])
print(f"arr2 = {arr2}")
print(f"mask2 = {mask2}")
print(f"mask2 type = {mask2.type}")

try:
    masked2 = ak.mask(arr2, mask2, valid_when=False)
    print(f"Success: masked2 = {masked2}")
except Exception as e:
    print(f"ERROR: {e}")