# Bug Report: statistics.quantiles() Returns Values Outside Data Range

**Target**: `statistics.quantiles`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `statistics.quantiles()` function with `method='exclusive'` (the default) returns quantile values that fall outside the minimum and maximum bounds of the input data when the sample size is small.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import statistics
import math

@given(
    st.lists(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False), min_size=1, max_size=100),
    st.integers(min_value=2, max_value=10)
)
def test_quantiles_within_bounds(data, n):
    """Test that quantiles are within data bounds."""
    quantiles = statistics.quantiles(data, n=n)
    data_min, data_max = min(data), max(data)
    for q in quantiles:
        assert data_min <= q <= data_max or math.isclose(q, data_min) or math.isclose(q, data_max)
```

**Failing input**: `data=[0.0, 1.0], n=4`

## Reproducing the Bug

```python
import statistics

data = [0.0, 1.0]
result = statistics.quantiles(data, n=4)
print(f"Data: {data}")
print(f"Data range: [{min(data)}, {max(data)}]")
print(f"Quantiles: {result}")
print(f"Values outside range: {[x for x in result if x < min(data) or x > max(data)]}")
```

Output:
```
Data: [0.0, 1.0]
Data range: [0.0, 1.0]
Quantiles: [-0.25, 0.5, 1.25]
Values outside range: [-0.25, 1.25]
```

## Why This Is A Bug

Quantiles are defined as values that divide a dataset into equal-probability intervals. By definition, these cut points should fall within the range of the observed data or at most be equal to the minimum or maximum values. Returning quantiles outside the data range violates this fundamental statistical property and can lead to incorrect interpretations and downstream errors in statistical analyses.

The bug occurs in the interpolation logic for `method='exclusive'` when dealing with small sample sizes. The calculation produces negative delta values or delta values greater than n, causing the interpolation formula to extrapolate beyond the data boundaries.

## Fix

```diff
--- a/statistics.py
+++ b/statistics.py
@@ -1095,7 +1095,11 @@ def quantiles(data, *, n=4, method='exclusive'):
             j = i * m // n                               # rescale i to m/n
             j = 1 if j < 1 else ld-1 if j > ld-1 else j  # clamp to 1 .. ld-1
             delta = i*m - j*n                            # exact integer math
-            interpolated = (data[j - 1] * (n - delta) + data[j] * delta) / n
+            # Ensure delta is within valid range for interpolation
+            if delta < 0:
+                interpolated = data[j - 1]
+            elif delta > n:
+                interpolated = data[j]
+            else:
+                interpolated = (data[j - 1] * (n - delta) + data[j] * delta) / n
             result.append(interpolated)
         return result
```

Alternatively, the clamping logic could be adjusted to ensure delta always falls within [0, n], or the entire interpolation approach could be reconsidered for edge cases with small sample sizes.