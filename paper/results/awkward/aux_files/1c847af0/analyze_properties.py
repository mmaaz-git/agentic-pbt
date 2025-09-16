#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import inspect
import awkward as ak

# Let's examine specific functions for properties
print("Analyzing potential properties in awkward.highlevel")
print("=" * 60)

# 1. Round-trip properties
print("\n1. ROUND-TRIP PROPERTIES:")
print("-" * 40)

# to_list / from_iter round-trip
print("\n  to_list / from_iter:")
try:
    arr = ak.Array([[1, 2], [], [3, 4, 5]])
    list_form = arr.to_list()
    reconstructed = ak.from_iter(list_form)
    print(f"    Original: {arr}")
    print(f"    to_list: {list_form}")
    print(f"    from_iter: {reconstructed}")
    print(f"    Round-trip works: {ak.array_equal(arr, reconstructed)}")
except Exception as e:
    print(f"    Error: {e}")

# to_numpy / from_numpy round-trip (for regular arrays)
print("\n  to_numpy / from_numpy (regular):")
try:
    arr = ak.Array([[1, 2, 3], [4, 5, 6]])
    numpy_form = ak.to_numpy(arr)
    reconstructed = ak.from_numpy(numpy_form)
    print(f"    Original: {arr}")
    print(f"    to_numpy: {numpy_form}")
    print(f"    from_numpy: {reconstructed}")
    print(f"    Round-trip works: {ak.array_equal(arr, reconstructed)}")
except Exception as e:
    print(f"    Error: {e}")

# 2. Invariant properties
print("\n\n2. INVARIANT PROPERTIES:")
print("-" * 40)

# flatten preserves total number of elements
print("\n  flatten preserves element count:")
arr = ak.Array([[1, 2], [], [3, 4, 5]])
flat = ak.flatten(arr)
print(f"    Original: {arr}")
print(f"    Flattened: {flat}")
print(f"    Sum before: {ak.sum(ak.count(arr, axis=1))}")
print(f"    Count after: {ak.count(flat)}")

# sort preserves elements
print("\n  sort preserves elements:")
arr = ak.Array([3, 1, 4, 1, 5, 9, 2, 6])
sorted_arr = ak.sort(arr)
print(f"    Original: {arr}")
print(f"    Sorted: {sorted_arr}")
print(f"    Same elements: {set(arr.to_list()) == set(sorted_arr.to_list())}")

# concatenate length property
print("\n  concatenate length:")
arr1 = ak.Array([1, 2, 3])
arr2 = ak.Array([4, 5])
concatenated = ak.concatenate([arr1, arr2])
print(f"    Array 1: {arr1} (len={len(arr1)})")
print(f"    Array 2: {arr2} (len={len(arr2)})")
print(f"    Concatenated: {concatenated} (len={len(concatenated)})")
print(f"    Length property: {len(concatenated) == len(arr1) + len(arr2)}")

# 3. Array class specific properties
print("\n\n3. ARRAY CLASS PROPERTIES:")
print("-" * 40)

# mask property
print("\n  mask operation:")
arr = ak.Array([1, 2, 3, 4, 5])
mask = ak.Array([True, False, True, False, True])
masked = arr.mask[mask]
print(f"    Array: {arr}")
print(f"    Mask: {mask}")
print(f"    Masked: {masked}")
print(f"    Length preserved: {len(masked) == len(arr)}")

# field access property for records
print("\n  field access for records:")
records = ak.Array([{"x": 1, "y": 2}, {"x": 3, "y": 4}])
print(f"    Records: {records}")
print(f"    Field 'x': {records.x}")
print(f"    Field 'y': {records['y']}")
print(f"    Equivalence: {ak.array_equal(records.x, records['x'])}")

# type preservation through operations
print("\n  type preservation:")
arr = ak.Array([[1, 2], [], [3, 4, 5]])
print(f"    Original type: {arr.type}")
print(f"    After +10 type: {(arr + 10).type}")

# Let's check docstrings for claimed properties
print("\n\n4. CHECKING DOCSTRINGS FOR PROPERTIES:")
print("-" * 40)

functions_to_check = ['flatten', 'sort', 'concatenate', 'zip', 'unzip']
for func_name in functions_to_check:
    func = getattr(ak, func_name)
    if func.__doc__:
        print(f"\n  {func_name}:")
        # Get first few lines of docstring
        lines = func.__doc__.split('\n')[:5]
        for line in lines:
            if line.strip():
                print(f"    {line.strip()}")