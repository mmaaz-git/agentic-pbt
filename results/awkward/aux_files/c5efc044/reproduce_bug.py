#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward as ak

# Reproduce the bug from the failing test
print("=== Reproducing the bug ===\n")

# Create initial RecordArray with 4 elements
initial_array = ak.contents.RecordArray(
    [
        ak.contents.NumpyArray(np.array([10, 20, 30, 40], dtype=np.int32)),
        ak.contents.NumpyArray(np.array([50, 60, 70, 80], dtype=np.int32))
    ],
    fields=None  # tuple-like
)

# Create a Record at position 3 (valid for initial_array with length 4)
record = ak.record.Record(initial_array, at=3)
print(f"Created record at position {record.at} from array with length {initial_array.length}")
print(f"Record contents: {record.to_list()}\n")

# Create a new array with only 3 elements  
new_array = ak.contents.RecordArray(
    [ak.contents.NumpyArray(np.array([99, 98, 97], dtype=np.int32))],
    fields=["x"]
)
print(f"New array has length {new_array.length}")

# Try to copy the record with the new array
# This should fail because at=3 is out of bounds for new_array (length=3)
print("\nAttempting to copy record with new array...")
try:
    new_record = record.copy(array=new_array)
    print(f"SUCCESS: Created new record (unexpected!)")
except ValueError as e:
    print(f"FAILED with ValueError: {e}")

print("\n=== Analysis ===")
print("The bug: Record.copy() doesn't validate that the existing 'at' value")
print("is valid for the new array when copying with a different array.")
print("This violates the invariant that 0 <= at < array.length")