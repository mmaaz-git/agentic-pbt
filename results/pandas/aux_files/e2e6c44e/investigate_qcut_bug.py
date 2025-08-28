import pandas as pd
import numpy as np

# Test the failing case from hypothesis
values = [0.0, 2.2250738585e-313]
bins = 2

print("Testing pd.qcut with tiny float value")
print(f"Values: {values}")
print(f"Bins: {bins}")

try:
    result = pd.qcut(values, q=bins, duplicates='drop')
    print("Result:", result)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Let's also test with a slightly different value
values2 = [0.0, 2.225073858507e-311]
print(f"\nTesting with values: {values2}")
try:
    result2 = pd.qcut(values2, q=bins, duplicates='drop')
    print("Result:", result2)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Let's see what the breaks are
print("\nInvestigating the breaks...")
import pandas.core.reshape.tile as tile

x = pd.Series(values)
_, bins_out = tile._bins_to_cuts(x, bins, duplicates='drop')
print(f"Bins generated: {bins_out}")

# Check if there's a NaN issue
print(f"Contains NaN: {np.any(np.isnan(bins_out))}")
print(f"Contains inf: {np.any(np.isinf(bins_out))}")

# Let's also examine the IntervalArray directly
from pandas import IntervalIndex
try:
    ii = IntervalIndex.from_breaks(bins_out, closed='right')
    print("IntervalIndex created successfully:", ii)
except Exception as e:
    print(f"IntervalIndex creation failed: {e}")
    print(f"Breaks array: {bins_out}")
    print(f"Breaks dtype: {bins_out.dtype}")
    print(f"Breaks shape: {bins_out.shape}")