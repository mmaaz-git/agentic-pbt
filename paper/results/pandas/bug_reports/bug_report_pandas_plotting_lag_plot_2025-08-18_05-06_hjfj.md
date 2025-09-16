# Bug Report: pandas.plotting.lag_plot ValueError with lag=0

**Target**: `pandas.plotting.lag_plot`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`lag_plot` raises a ValueError when called with `lag=0` due to incorrect array slicing that produces mismatched array sizes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
import numpy as np
from pandas.plotting import lag_plot

@given(
    series_length=st.integers(min_value=2, max_value=100),
    lag=st.integers(min_value=-100, max_value=100)
)
def test_lag_plot_negative_lag(series_length, lag):
    series = pd.Series(np.random.randn(series_length))
    
    if lag < 0 or lag >= series_length:
        try:
            ax = lag_plot(series, lag=lag)
            assert ax is not None
        except (ValueError, IndexError, TypeError) as e:
            pass
    else:
        ax = lag_plot(series, lag=lag)
        assert ax is not None
```

**Failing input**: `series_length=2, lag=0`

## Reproducing the Bug

```python
import matplotlib
matplotlib.use('Agg')
import pandas as pd
from pandas.plotting import lag_plot

series = pd.Series([1, 2])
ax = lag_plot(series, lag=0)
```

## Why This Is A Bug

The function should either handle `lag=0` gracefully (plotting y(t) vs y(t), which would be a diagonal line) or raise a clear error message explaining that lag must be positive. Instead, it fails with an obscure "x and y must be the same size" error due to a slicing issue where `data[:-0]` returns an empty array rather than the full array.

## Fix

```diff
--- a/pandas/plotting/_matplotlib/misc.py
+++ b/pandas/plotting/_matplotlib/misc.py
@@ -431,8 +431,11 @@ def lag_plot(series: Series, lag: int = 1, ax: Axes | None = None, **kwds) -> A
     kwds.setdefault("c", plt.rcParams["patch.facecolor"])
 
     data = series.values
-    y1 = data[:-lag]
-    y2 = data[lag:]
+    if lag == 0:
+        y1 = data
+        y2 = data
+    else:
+        y1 = data[:-lag] if lag > 0 else data[-lag:]
+        y2 = data[lag:] if lag > 0 else data[:lag]
     if ax is None:
         ax = plt.gca()
     ax.set_xlabel("y(t)")
```