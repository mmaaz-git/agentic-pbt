#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

print("Investigating iteration behavior")
print("=" * 60)

# The failing example from Hypothesis
arr = ak.Array([0])
print(f"Array: {arr}")
print(f"Type: {arr.type}")
print(f"to_list(): {arr.to_list()}")

print("\nIterating over the array:")
for i, item in enumerate(arr):
    print(f"  Item {i}: {item}")
    print(f"  Item type: {type(item)}")
    print(f"  Item value: {item}")
    
print("\n" + "=" * 60)
print("Testing with different array structures:")

# Test 1: Simple flat array
arr1 = ak.Array([1, 2, 3])
print(f"\nFlat array: {arr1}")
print(f"Type: {arr1.type}")
print("Items from iteration:")
for item in arr1:
    print(f"  {item} (type: {type(item)})")
print(f"to_list(): {arr1.to_list()}")

# Test 2: Nested array  
arr2 = ak.Array([[1, 2], [3]])
print(f"\nNested array: {arr2}")
print(f"Type: {arr2.type}")
print("Items from iteration:")
for item in arr2:
    print(f"  {item} (type: {type(item)})")
    if hasattr(item, 'to_list'):
        print(f"    to_list(): {item.to_list()}")
    else:
        print(f"    No to_list method")
print(f"to_list(): {arr2.to_list()}")

# Test 3: Deeply nested
arr3 = ak.Array([[[1, 2]], [[3]], []])
print(f"\nDeeply nested array: {arr3}")
print(f"Type: {arr3.type}")
print("Items from iteration:")
for item in arr3:
    print(f"  {item} (type: {type(item)})")
    if hasattr(item, 'to_list'):
        print(f"    to_list(): {item.to_list()}")
print(f"to_list(): {arr3.to_list()}")

# Check the documentation claim
print("\n" + "=" * 60)
print("Checking if iteration behavior matches documentation:")
print("-" * 60)

# According to the code, iteration should wrap items
arr = ak.Array([[1, 2], [3, 4, 5]])
print(f"Array: {arr}")

print("\nManual iteration vs to_list:")
manual_list = []
for item in arr:
    if hasattr(item, 'to_list'):
        manual_list.append(item.to_list())
    else:
        # This is a scalar
        if hasattr(item, 'item'):
            manual_list.append(item.item())
        else:
            manual_list.append(item)

print(f"Manual iteration result: {manual_list}")
print(f"to_list() result: {arr.to_list()}")
print(f"Match: {manual_list == arr.to_list()}")

# Edge case: what about scalars from a 1D array?
print("\n" + "=" * 60)
print("Edge case: Scalars from 1D array iteration")
arr_1d = ak.Array([10, 20, 30])
print(f"1D Array: {arr_1d}")
for i, item in enumerate(arr_1d):
    print(f"  Item {i}: {item}, type: {type(item)}, is numpy scalar: {isinstance(item, np.number)}")