"""Investigate the None vs NaN factorize bug"""

import numpy as np
import pandas as pd
from pandas.core.algorithms import factorize

# Test case from hypothesis
values = [None, float('nan')]
arr = np.array(values, dtype=object)

print("Original array:", arr)
print("Array dtype:", arr.dtype)

# Test with use_na_sentinel=False
codes, uniques = factorize(arr, use_na_sentinel=False)

print("\nWith use_na_sentinel=False:")
print("Codes:", codes)
print("Uniques:", uniques)
print("Uniques type:", type(uniques))

# Check what's in uniques
print("\nAnalyzing uniques:")
for i, val in enumerate(uniques):
    print(f"  uniques[{i}] = {val}, type = {type(val)}, is None? {val is None}, is NaN? {pd.isna(val)}")

# Count None and NaN
none_count = sum(1 for v in values if v is None)
nan_count = sum(1 for v in values if isinstance(v, float) and pd.isna(v))
print(f"\nOriginal: {none_count} None, {nan_count} NaN")

unique_none_count = sum(1 for v in uniques if v is None)
unique_nan_count = sum(1 for v in uniques if isinstance(v, float) and pd.isna(v))
print(f"Uniques: {unique_none_count} None, {unique_nan_count} NaN")

# Test reconstruction
if isinstance(uniques, pd.Index):
    reconstructed = np.array(uniques.take(codes))
else:
    reconstructed = uniques.take(codes)

print("\nReconstructed array:", reconstructed)

# Check if None and NaN are treated as the same
print("\n=== BUG: None and NaN are conflated! ===")
print(f"Original has both None and NaN, but uniques has only one of them.")
print(f"This means factorize treats None and NaN as the same value in object arrays.")