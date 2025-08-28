#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np

print("=" * 60)
print("BUG 1: Negative indexing beyond bounds")
print("=" * 60)

# Test with Python list
py_list = [1, 2, 3]
print(f"Python list: {py_list}")
print(f"  py_list[-1]: {py_list[-1]}")
print(f"  py_list[-3]: {py_list[-3]}")
try:
    print(f"  py_list[-4]: {py_list[-4]}")
except IndexError as e:
    print(f"  py_list[-4]: IndexError: {e}")
try:
    print(f"  py_list[-1000]: {py_list[-1000]}")
except IndexError as e:
    print(f"  py_list[-1000]: IndexError: {e}")

# Test with NumPy array
np_array = np.array([1, 2, 3])
print(f"\nNumPy array: {np_array}")
print(f"  np_array[-1]: {np_array[-1]}")
print(f"  np_array[-3]: {np_array[-3]}")
try:
    print(f"  np_array[-4]: {np_array[-4]}")
except IndexError as e:
    print(f"  np_array[-4]: IndexError: {e}")
try:
    print(f"  np_array[-1000]: {np_array[-1000]}")
except IndexError as e:
    print(f"  np_array[-1000]: IndexError: {e}")

# Test with Awkward Array
ak_array = ak.Array([1, 2, 3])
print(f"\nAwkward Array: {ak_array}")
print(f"  ak_array[-1]: {ak_array[-1]}")
print(f"  ak_array[-3]: {ak_array[-3]}")
try:
    print(f"  ak_array[-4]: {ak_array[-4]}")
except IndexError as e:
    print(f"  ak_array[-4]: IndexError: {e}")
try:
    print(f"  ak_array[-1000]: {ak_array[-1000]}")
except IndexError as e:
    print(f"  ak_array[-1000]: IndexError: {e}")

print("\n" + "=" * 60)
print("BUG 2: Mask with all True changes type")
print("=" * 60)

# Test masking with all True
arr = ak.Array([1, 2, 3, 4, 5])
print(f"Original array: {arr}")
print(f"  Type: {arr.type}")
print(f"  dtype: {arr.dtype if hasattr(arr, 'dtype') else 'N/A'}")

# Create all True mask
all_true_mask = ak.Array([True, True, True, True, True])
print(f"\nAll-True mask: {all_true_mask}")

# Apply mask
masked = arr.mask[all_true_mask]
print(f"\nMasked array: {masked}")
print(f"  Type: {masked.type}")
print(f"  dtype: {masked.dtype if hasattr(masked, 'dtype') else 'N/A'}")

# Check values
print(f"\nValues comparison:")
print(f"  Original values: {arr.to_list()}")
print(f"  Masked values: {masked.to_list()}")
print(f"  Are they equal (values)? {arr.to_list() == masked.to_list()}")
print(f"  Are they equal (arrays)? {ak.array_equal(arr, masked)}")

# Check for None values
print(f"\nNone check:")
print(f"  Any None in original? {ak.any(ak.is_none(arr))}")
print(f"  Any None in masked? {ak.any(ak.is_none(masked))}")

# Test with mixed mask
print("\n" + "-" * 40)
print("Comparison with mixed mask:")
mixed_mask = ak.Array([True, False, True, False, True])
masked_mixed = arr.mask[mixed_mask]
print(f"Mixed mask: {mixed_mask}")
print(f"Masked with mixed: {masked_mixed}")
print(f"  Type: {masked_mixed.type}")

# Test filtering vs masking
print("\n" + "-" * 40)
print("Filtering vs Masking:")
filtered = arr[all_true_mask]
print(f"Filtered (arr[mask]): {filtered}")
print(f"  Type: {filtered.type}")
print(f"Masked (arr.mask[mask]): {masked}")
print(f"  Type: {masked.type}")

# Check documentation or expected behavior
print("\n" + "=" * 60)
print("Expected behavior check:")
print("=" * 60)

print("According to the documentation, arr.mask[mask] should:")
print("- Preserve the array length")
print("- Insert None where mask is False")
print("- Keep original values where mask is True")
print("\nThe issue is that even with all True mask, the type changes to option type.")
print("This might be by design, but it's inconsistent with filtering behavior.")