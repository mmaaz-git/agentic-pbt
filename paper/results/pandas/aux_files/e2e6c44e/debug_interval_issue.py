import pandas as pd
import numpy as np
from pandas.core.arrays.interval import IntervalArray

# Reproduce the internal issue
values = [0.0, 2.2250738585e-313]
s = pd.Series(values)

# Simulate what qcut does internally
quantiles = np.linspace(0, 1, 3)  # For 2 bins, we need 3 edges
bin_edges = s.quantile(quantiles).values
print(f"Bin edges: {bin_edges}")
print(f"Bin edges dtype: {bin_edges.dtype}")

# Check for NaN or inf
print(f"Contains NaN: {np.any(np.isnan(bin_edges))}")
print(f"Contains inf: {np.any(np.isinf(bin_edges))}")

# Now try to create the IntervalArray
left = bin_edges[:-1]
right = bin_edges[1:]
print(f"\nLeft edges: {left}")
print(f"Right edges: {right}")

# Check what _validate does
left_mask = pd.isna(left)
right_mask = pd.isna(right)

print(f"\nLeft NaN mask: {left_mask}")
print(f"Right NaN mask: {right_mask}")

# The error occurs when these masks don't match
if not (left_mask == right_mask).all():
    print("ERROR: NaN masks don't match!")
    print("This is the bug - qcut produces intervals where NaN appears in different positions")

# Let's see what's causing the NaN
print(f"\nDetailed analysis:")
print(f"Is 0.0 NaN? {pd.isna(0.0)}")
print(f"Is {bin_edges[0]} NaN? {pd.isna(bin_edges[0])}")
print(f"Is {bin_edges[1]} NaN? {pd.isna(bin_edges[1])}")
print(f"Is {bin_edges[2]} NaN? {pd.isna(bin_edges[2])}")

# The issue is likely that the middle quantile calculation produces a problematic value
# when dealing with subnormal floats