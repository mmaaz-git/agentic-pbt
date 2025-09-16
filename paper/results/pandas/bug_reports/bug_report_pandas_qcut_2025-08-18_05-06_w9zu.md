# Bug Report: pandas.qcut Fails on Subnormal Float Values

**Target**: `pandas.qcut`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `pd.qcut` function crashes with a ValueError when processing arrays containing subnormal float values (values smaller than `np.finfo(float).tiny`), even though these are valid floating-point numbers that can occur in real pandas usage.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd

@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000), min_size=2),
    st.integers(min_value=2, max_value=10)
)
def test_qcut_preserve_length(values, bins):
    """Test that qcut preserves input length"""
    assume(bins <= len(values))
    
    qcut_result = pd.qcut(values, q=bins, duplicates='drop')
    assert len(qcut_result) == len(values)
```

**Failing input**: `values=[0.0, 2.2250738585e-313], bins=2`

## Reproducing the Bug

```python
import pandas as pd
import numpy as np

values = [0.0, 2.2250738585e-313]

result = pd.qcut(values, q=2, duplicates='drop')
```

## Why This Is A Bug

The function should handle all valid floating-point numbers, including subnormal values. Subnormal floats can arise from:
1. Reading data from CSV files
2. Mathematical operations that produce very small results
3. User-created data

The error "missing values must be missing in the same location both left and right sides" indicates an internal inconsistency in how pandas processes these edge-case values when creating interval bins. The function produces a RuntimeWarning about "invalid value encountered in divide" before crashing, suggesting numerical instability in the binning logic.

## Fix

The issue appears to be in the interval creation logic within `pandas/core/reshape/tile.py`. When processing subnormal floats, the bin edge calculation produces inconsistent NaN placements. A potential fix would be to add special handling for subnormal values:

```diff
--- a/pandas/core/reshape/tile.py
+++ b/pandas/core/reshape/tile.py
@@ -570,6 +570,10 @@ def _format_labels(
         # adjust lhs of first interval by precision to account for being right closed
         breaks[0] = adjust(breaks[0])
 
+    # Handle subnormal floats to avoid interval creation issues
+    if breaks.dtype.kind == 'f':
+        breaks = np.where(np.abs(breaks) < np.finfo(breaks.dtype).tiny, 0.0, breaks)
+
     if _is_dt_or_td(bins.dtype):
         # error: "Index" has no attribute "as_unit"
         breaks = type(bins)(breaks).as_unit(unit)  # type: ignore[attr-defined]
```