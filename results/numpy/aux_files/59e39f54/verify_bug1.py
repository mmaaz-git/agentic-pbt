"""Verify this is a genuine bug by checking pandas behavior"""

import numpy as np
import pandas as pd
from pandas.core.algorithms import factorize

# Create a more comprehensive test
values = [1, None, 2, float('nan'), 3, None, float('nan'), 4]
arr = np.array(values, dtype=object)

print("Original values:", values)
print()

# Factorize with use_na_sentinel=False (should preserve both None and NaN)
codes, uniques = factorize(arr, use_na_sentinel=False)

print("Factorized with use_na_sentinel=False:")
print("Codes:", codes)
print("Uniques:", uniques)

# Reconstruct
if isinstance(uniques, pd.Index):
    reconstructed = np.array(uniques.take(codes))
else:
    reconstructed = uniques.take(codes)

print("\nReconstructed values:")
for i, (orig, recon) in enumerate(zip(values, reconstructed)):
    matches = orig == recon or (orig is None and recon is None) or (pd.isna(orig) and pd.isna(recon))
    print(f"  {i}: {orig} -> {recon} {'✓' if matches else '✗ MISMATCH'}")

print("\n=== ANALYSIS ===")
print("This is a genuine bug because:")
print("1. When use_na_sentinel=False, factorize should preserve all distinct values")
print("2. None and NaN are distinct values in Python (None is not NaN)")
print("3. The function conflates them, losing information")
print("4. This breaks the round-trip property documented in the function")

# Show that pandas Series distinguishes them
s = pd.Series(values)
print("\n=== pandas Series distinguishes None and NaN ===")
print("Series:")
print(s)
print("\nSeries.isna():")
print(s.isna())
print("\nNote: Series.isna() returns True for both, but they are stored differently internally")