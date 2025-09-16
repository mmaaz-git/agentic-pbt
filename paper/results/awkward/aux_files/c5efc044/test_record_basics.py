#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

# Create a simple RecordArray to understand how it works
print("=== Creating RecordArray and Records ===")
rec_array = ak.contents.RecordArray(
    [
        ak.contents.NumpyArray(np.array([1, 2, 3])),
        ak.contents.NumpyArray(np.array([4.5, 6.7, 8.9]))
    ],
    fields=["x", "y"]
)

print(f"RecordArray: {rec_array}")
print(f"RecordArray length: {rec_array.length}")
print(f"RecordArray fields: {rec_array.fields}")

# Create Record instances
print("\n=== Creating Record instances ===")
rec0 = ak.record.Record(rec_array, 0)
rec1 = ak.record.Record(rec_array, 1)
rec2 = ak.record.Record(rec_array, 2)

print(f"rec0: {rec0}")
print(f"rec0.fields: {rec0.fields}")
print(f"rec0['x']: {rec0['x']}")
print(f"rec0['y']: {rec0['y']}")
print(f"rec0.contents: {rec0.contents}")

# Test copy
print("\n=== Testing copy ===")
rec0_copy = rec0.copy()
print(f"rec0_copy is rec0: {rec0_copy is rec0}")
print(f"rec0_copy.array is rec0.array: {rec0_copy.array is rec0.array}")
print(f"rec0_copy.at == rec0.at: {rec0_copy.at == rec0.at}")

# Test to_list
print("\n=== Testing to_list ===")
print(f"rec0.to_list(): {rec0.to_list()}")

# Test with tuple-like records
print("\n=== Testing tuple records ===")
tuple_array = ak.contents.RecordArray(
    [
        ak.contents.NumpyArray(np.array([10, 20, 30])),
        ak.contents.NumpyArray(np.array([40, 50, 60]))
    ],
    fields=None  # tuple-like
)
tuple_rec = ak.record.Record(tuple_array, 1)
print(f"tuple_rec.is_tuple: {tuple_rec.is_tuple}")
print(f"tuple_rec.to_list(): {tuple_rec.to_list()}")

# Test edge cases
print("\n=== Testing bounds ===")
try:
    bad_rec = ak.record.Record(rec_array, 3)  # out of bounds
    print("Created out of bounds record (should have failed)")
except ValueError as e:
    print(f"Out of bounds error (expected): {e}")

try:
    bad_rec = ak.record.Record(rec_array, -1)  # negative index
    print("Created negative index record (should have failed)")
except ValueError as e:
    print(f"Negative index error (expected): {e}")