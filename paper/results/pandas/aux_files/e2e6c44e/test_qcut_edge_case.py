import pandas as pd
import numpy as np

# Test various edge cases with qcut
test_cases = [
    ([0.0, 2.2250738585e-313], 2, "Subnormal float"),
    ([0.0, 1e-320], 2, "Even smaller float"),
    ([0.0, np.finfo(float).tiny], 2, "Smallest normal float"),
    ([0.0, np.finfo(float).min], 2, "Most negative float"),
    ([0.0, 0.0], 2, "Duplicate zeros"),
]

for values, bins, description in test_cases:
    print(f"\n{description}:")
    print(f"  Values: {values}")
    try:
        result = pd.qcut(values, q=bins, duplicates='drop')
        print(f"  Success: {result.tolist()}")
    except ValueError as e:
        print(f"  ValueError: {e}")
    except Exception as e:
        print(f"  {type(e).__name__}: {e}")

# Let's trace through what happens step by step for the failing case
print("\n\nDetailed trace for [0.0, 2.2250738585e-313]:")
values = [0.0, 2.2250738585e-313]

import pandas.core.reshape.tile as tile
import pandas.core.algorithms as algos
from pandas import Series

x = Series(values)
q = 2

# This is what qcut does
quantiles = np.linspace(0, 1, q + 1)
print(f"Quantiles: {quantiles}")

# Get bin edges
bin_edges = algos.quantile(x, quantiles)
print(f"Bin edges: {bin_edges}")

# Check for duplicates
print(f"Unique bin edges: {np.unique(bin_edges)}")

# The _bins_to_cuts function
# _bins_to_cuts internally calls _format_labels which calls IntervalIndex.from_breaks
try:
    fac, bins_out = tile._bins_to_cuts(x, q, duplicates='drop')
    print(f"Success from _bins_to_cuts")
    print(f"Bins: {bins_out}")
except Exception as e:
    print(f"Failed in _bins_to_cuts: {e}")
    import traceback
    traceback.print_exc()