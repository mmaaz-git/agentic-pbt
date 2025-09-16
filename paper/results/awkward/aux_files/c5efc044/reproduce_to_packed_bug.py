#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward as ak

print("=== Reproducing to_packed bug ===\n")

# Create a RecordArray with multiple elements
array = ak.contents.RecordArray(
    [
        ak.contents.NumpyArray(np.array([10, 20, 30, 40, 50])),
        ak.contents.NumpyArray(np.array([100, 200, 300, 400, 500]))
    ],
    fields=None  # tuple-like
)

print(f"Array length: {array.length}")
print(f"Array fields: {array.fields}")

# Create a Record at position 4
record = ak.record.Record(array, at=4)
print(f"\nOriginal record at position: {record.at}")
print(f"Original record contents: {record.to_list()}")

# Call to_packed
packed = record.to_packed()
print(f"\nPacked record at position: {packed.at}")
print(f"Packed record contents: {packed.to_list()}")

print("\n=== Analysis ===")
print("The bug: to_packed() changes the 'at' position from 4 to 0")
print("This violates the expectation that packing should preserve the record's position")
print("Looking at the code (lines 196-200 in record.py):")
print("  - If array.length == 1, it keeps the original record")
print("  - Otherwise, it creates a slice [at:at+1] and packs that, setting at=0")
print("This means the packed record loses its original position information!")

# Let's verify this is the implementation
print("\n=== Verification ===")
print(f"record.array.length: {record.array.length}")
print(f"Is record.array.length == 1? {record.array.length == 1}")
print(f"So it takes the else branch: Record(array[at:at+1].to_packed(), 0)")

# What the sliced array looks like
sliced = record.array[record.at : record.at + 1]
print(f"\nSliced array length: {sliced.length}")
print(f"Sliced array: {sliced}")

print("\n=== Impact ===")
print("This bug means that after calling to_packed():")
print("1. The record's 'at' property changes unexpectedly")
print("2. Code that relies on maintaining position will break")
print("3. The invariant that operations preserve 'at' is violated")