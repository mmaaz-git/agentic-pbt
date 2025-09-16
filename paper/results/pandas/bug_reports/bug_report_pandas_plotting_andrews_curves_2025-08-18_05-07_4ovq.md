# Bug Report: pandas.plotting.andrews_curves Accepts samples=0 Creating Empty Plot

**Target**: `pandas.plotting.andrews_curves`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

`andrews_curves` accepts `samples=0` without validation, resulting in an empty plot with no data points, which violates the expected behavior of generating curves.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
from pandas.plotting import andrews_curves

@given(samples=st.integers(min_value=-100, max_value=100))
def test_andrews_curves_samples_validation(samples):
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'class': ['a', 'b', 'c']
    })
    
    if samples <= 0:
        with pytest.raises((ValueError, TypeError)):
            andrews_curves(df, 'class', samples=samples)
    else:
        ax = andrews_curves(df, 'class', samples=samples)
        assert ax is not None
```

**Failing input**: `samples=0`

## Reproducing the Bug

```python
import matplotlib
matplotlib.use('Agg')
import pandas as pd
from pandas.plotting import andrews_curves

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'class': ['a', 'b', 'c']
})

ax = andrews_curves(df, 'class', samples=0)
lines = ax.get_lines()
print(f"Lines plotted: {len(lines)}")
print(f"Points in first line: {len(lines[0].get_xdata())}")
```

## Why This Is A Bug

Andrews curves are meant to visualize multivariate data by mapping each observation to a curve. With `samples=0`, no points are generated for the curves, resulting in empty lines being added to the plot. This is misleading and violates the function's contract. The function already validates negative samples (raises error for `samples < 0`), but fails to validate `samples == 0`.

## Fix

```diff
--- a/pandas/plotting/_matplotlib/misc.py
+++ b/pandas/plotting/_matplotlib/misc.py
@@ -156,8 +156,8 @@ def andrews_curves(
     import matplotlib.pyplot as plt
 
     n = len(frame)
-    if samples < 0:
-        raise ValueError(f"Number of samples, {samples}, must be non-negative.")
+    if samples <= 0:
+        raise ValueError(f"Number of samples, {samples}, must be positive.")
 
     class_col = frame[class_column]
     classes = class_col.drop_duplicates()
```