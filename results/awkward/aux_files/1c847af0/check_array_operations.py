#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

print("Testing Array class operations for properties")
print("=" * 60)

# 1. Test __getitem__ slicing properties
print("\n1. SLICING PROPERTIES:")
print("-" * 40)

# Identity slicing
arr = ak.Array([[1, 2, 3], [], [4, 5]])
print(f"  Original: {arr}")
print(f"  arr[:]: {arr[:]}")
print(f"  Identity property: {ak.array_equal(arr, arr[:])}")

# Double negative indexing
arr = ak.Array([1, 2, 3, 4, 5])
print(f"\n  Array: {arr}")
print(f"  arr[-2]: {arr[-2]}")
print(f"  arr[len(arr)-2]: {arr[len(arr)-2]}")
print(f"  Negative index property: {arr[-2] == arr[len(arr)-2]}")

# 2. Test iteration properties
print("\n\n2. ITERATION PROPERTIES:")
print("-" * 40)

arr = ak.Array([[1, 2], [3], [4, 5, 6]])
print(f"  Array: {arr}")
print(f"  List from iteration: {[x.to_list() for x in arr]}")
print(f"  to_list(): {arr.to_list()}")
print(f"  Equivalence: {[x.to_list() for x in arr] == arr.to_list()}")

# 3. Test field operations for records
print("\n\n3. RECORD FIELD OPERATIONS:")
print("-" * 40)

# Setting and getting fields
records = ak.Array([{"x": 1}, {"x": 2}, {"x": 3}])
print(f"  Original records: {records}")
records["y"] = records["x"] * 2
print(f"  After adding field 'y': {records}")
print(f"  Field relationship: y = 2*x holds: {ak.all(records.y == 2 * records.x)}")

# Deleting fields
del records["y"]
print(f"  After deleting 'y': {records}")

# 4. Test mask operations
print("\n\n4. MASK OPERATIONS:")
print("-" * 40)

arr = ak.Array([1, 2, 3, 4, 5])
mask = arr > 2
print(f"  Array: {arr}")
print(f"  Mask (>2): {mask}")
print(f"  Filtered: {arr[mask]}")
print(f"  Masked: {arr.mask[mask]}")
print(f"  Mask preserves length: {len(arr.mask[mask]) == len(arr)}")

# 5. Test nested array operations
print("\n\n5. NESTED ARRAY OPERATIONS:")
print("-" * 40)

nested = ak.Array([[[1, 2], [3]], [], [[4, 5, 6]]])
print(f"  Nested array: {nested}")
print(f"  Type: {nested.type}")
print(f"  ndim: {nested.ndim}")

# Flattening at different levels
flat1 = ak.flatten(nested, axis=1)
flat2 = ak.flatten(nested, axis=2)
print(f"  Flatten axis=1: {flat1}")
print(f"  Flatten axis=2: {flat2}")

# 6. Test zip/unzip round-trip
print("\n\n6. ZIP/UNZIP ROUND-TRIP:")
print("-" * 40)

x = ak.Array([1, 2, 3])
y = ak.Array([4, 5, 6])
zipped = ak.zip({"x": x, "y": y})
print(f"  x: {x}")
print(f"  y: {y}")
print(f"  Zipped: {zipped}")
unzipped = ak.unzip(zipped)
print(f"  Unzipped: {unzipped}")
print(f"  Round-trip x: {ak.array_equal(x, unzipped[0])}")
print(f"  Round-trip y: {ak.array_equal(y, unzipped[1])}")

# 7. Test broadcasting properties
print("\n\n7. BROADCASTING PROPERTIES:")
print("-" * 40)

arr1 = ak.Array([[1, 2], [3, 4]])
scalar = 10
result = arr1 + scalar
print(f"  Array: {arr1}")
print(f"  Scalar: {scalar}")
print(f"  Array + Scalar: {result}")
print(f"  Shape preserved: {arr1.type == result.type.replace('int64', 'int64')}")

# 8. Check for idempotent operations
print("\n\n8. IDEMPOTENT OPERATIONS:")
print("-" * 40)

arr = ak.Array([3, 1, 4, 1, 5, 9, 2, 6])
sorted_once = ak.sort(arr)
sorted_twice = ak.sort(sorted_once)
print(f"  Original: {arr}")
print(f"  Sorted once: {sorted_once}")
print(f"  Sorted twice: {sorted_twice}")
print(f"  Idempotent: {ak.array_equal(sorted_once, sorted_twice)}")