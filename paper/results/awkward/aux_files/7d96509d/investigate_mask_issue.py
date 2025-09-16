#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

print("=== Investigating ak.mask Type Requirements ===\n")

# Test various scenarios
test_cases = [
    ("Empty int array, empty unknown mask", ak.Array([]), ak.Array([])),
    ("Empty int array, empty bool mask", ak.Array([]), ak.Array(np.array([], dtype=bool))),
    ("Non-empty int array, matching bool mask", ak.Array([1, 2]), ak.Array([True, False])),
    ("Non-empty int array, matching int mask", ak.Array([1, 2]), ak.Array([1, 0])),
    ("Empty arrays both unknown type", ak.Array([]), ak.Array([])),
]

for desc, arr, mask in test_cases:
    print(f"Test: {desc}")
    print(f"  Array type: {arr.type}")
    print(f"  Mask type: {mask.type}")
    try:
        result = ak.mask(arr, mask, valid_when=False)
        print(f"  Result: SUCCESS - {result}")
    except Exception as e:
        print(f"  Result: FAILED - {e}")
    print()

print("=== Key Finding ===")
print("ak.mask strictly requires boolean type for the mask parameter.")
print("Empty arrays created from Python lists have type '0 * unknown',")
print("which is rejected even though the array is empty and the operation")
print("would be logically valid (masking 0 elements with 0 mask values).")
print("\nThis is arguably too strict - the function could handle empty")
print("arrays of any type as masks when both arrays are empty.")