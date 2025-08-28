#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

print("=== Bug: Empty Array Type Issue with ak.mask ===\n")

# The issue: creating an empty array doesn't preserve boolean type information
print("1. Creating empty arrays:")
empty_list = []
empty_arr = ak.Array(empty_list)
print(f"   ak.Array([]) type: {empty_arr.type}")

# Try creating boolean array from numpy
empty_bool_np = np.array([], dtype=bool)
empty_bool_ak = ak.Array(empty_bool_np)
print(f"   ak.Array(np.array([], dtype=bool)) type: {empty_bool_ak.type}")

print("\n2. Attempting to use empty array as mask:")
try:
    # This should work but fails
    result = ak.mask(empty_arr, empty_bool_ak, valid_when=False)
    print(f"   Success: {result}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n3. The problem extends to any array creation from empty list:")
# Even when we try to create the mask from a boolean list, if it's empty it loses type
bool_list = []
mask_from_bool_list = ak.Array(bool_list)
print(f"   Empty boolean list becomes: {mask_from_bool_list.type}")

print("\n4. Contrast with non-empty case:")
bool_list_nonempty = [True, False]
mask_nonempty = ak.Array(bool_list_nonempty)
print(f"   [True, False] becomes: {mask_nonempty.type}")

print("\n5. Documentation expectation:")
print("   According to ak.mask documentation, 'mask' should be an 'array of booleans'")
print("   But empty arrays lose their boolean type information!")

print("\n6. This causes issues in property testing:")
print("   When testing with empty arrays (valid edge case), the mask operation fails")
print("   even though logically masking an empty array with an empty mask should work.")