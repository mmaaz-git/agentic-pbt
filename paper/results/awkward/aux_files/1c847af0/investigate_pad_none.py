#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

print("Investigating pad_none with empty arrays")
print("=" * 60)

# Test case 1: Empty array
empty = ak.Array([])
print(f"Empty array: {empty}")
print(f"  Type: {empty.type}")
print(f"  ndim: {empty.ndim}")

print("\nTrying pad_none with axis=0:")
try:
    padded0 = ak.pad_none(empty, 3, axis=0)
    print(f"  Success: {padded0}")
    print(f"  Type: {padded0.type}")
except Exception as e:
    print(f"  Error: {e}")

print("\nTrying pad_none with axis=1:")
try:
    padded1 = ak.pad_none(empty, 3, axis=1)
    print(f"  Success: {padded1}")
except Exception as e:
    print(f"  Error: {e}")

# Test case 2: Empty nested array
empty_nested = ak.Array([[], [], []])
print(f"\nEmpty nested array: {empty_nested}")
print(f"  Type: {empty_nested.type}")
print(f"  ndim: {empty_nested.ndim}")

print("\nTrying pad_none with axis=1:")
try:
    padded1 = ak.pad_none(empty_nested, 3, axis=1)
    print(f"  Success: {padded1}")
    print(f"  Type: {padded1.type}")
except Exception as e:
    print(f"  Error: {e}")

# Test case 3: Mixed empty and non-empty
mixed = ak.Array([[1, 2], [], [3]])
print(f"\nMixed array: {mixed}")
print(f"  Type: {mixed.type}")

print("\nTrying pad_none with axis=1:")
try:
    padded = ak.pad_none(mixed, 3, axis=1)
    print(f"  Success: {padded}")
    print(f"  Type: {padded.type}")
except Exception as e:
    print(f"  Error: {e}")

# Check what operations work on empty arrays
print("\n" + "=" * 60)
print("Other operations on empty arrays:")
print("=" * 60)

empty = ak.Array([])
print(f"Empty array: {empty}")

ops_to_test = [
    ("len", lambda x: len(x)),
    ("flatten", lambda x: ak.flatten(x)),
    ("sort", lambda x: ak.sort(x)),
    ("concatenate with self", lambda x: ak.concatenate([x, x])),
    ("to_list", lambda x: x.to_list()),
    ("num axis=0", lambda x: ak.num(x, axis=0)),
]

for name, op in ops_to_test:
    try:
        result = op(empty)
        print(f"  {name}: {result}")
    except Exception as e:
        print(f"  {name}: Error - {e}")

# Now test with empty nested
print(f"\nEmpty nested array: {empty_nested}")

for name, op in ops_to_test:
    try:
        result = op(empty_nested)
        print(f"  {name}: {result}")
    except Exception as e:
        print(f"  {name}: Error - {e}")