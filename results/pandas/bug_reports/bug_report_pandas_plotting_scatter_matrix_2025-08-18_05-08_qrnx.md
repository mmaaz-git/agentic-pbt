# Bug Report: pandas.plotting.scatter_matrix Silently Ignores Invalid diagonal Parameter

**Target**: `pandas.plotting.scatter_matrix`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

`scatter_matrix` silently accepts invalid values for the `diagonal` parameter, producing empty diagonal plots instead of raising an error to inform the user of the invalid input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
import numpy as np
from pandas.plotting import scatter_matrix

@given(
    df_rows=st.integers(min_value=2, max_value=50),
    df_cols=st.integers(min_value=2, max_value=5),
    diagonal=st.sampled_from(['hist', 'kde', None, 'invalid'])
)
def test_scatter_matrix_diagonal_validation(df_rows, df_cols, diagonal):
    df = pd.DataFrame(np.random.randn(df_rows, df_cols))
    
    if diagonal in ['hist', 'kde', None]:
        axes = scatter_matrix(df, diagonal=diagonal)
        assert axes is not None
    elif diagonal == 'invalid':
        with pytest.raises((ValueError, KeyError, TypeError)):
            scatter_matrix(df, diagonal=diagonal)
```

**Failing input**: `diagonal='invalid'`

## Reproducing the Bug

```python
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
from pandas.plotting import scatter_matrix

df = pd.DataFrame(np.random.randn(3, 3), columns=['A', 'B', 'C'])

axes = scatter_matrix(df, diagonal='invalid')
print("No error raised for diagonal='invalid'")

ax_diagonal = axes[0, 0]
print(f"Diagonal plot has {len(ax_diagonal.patches)} bars and {len(ax_diagonal.lines)} lines")
```

## Why This Is A Bug

The `diagonal` parameter should only accept 'hist', 'kde', or None. When an invalid value is provided, the function should raise a ValueError to inform the user, similar to how other plotting functions validate their parameters. Instead, it silently creates empty diagonal plots, which can be confusing and makes debugging harder.

## Fix

```diff
--- a/pandas/plotting/_matplotlib/misc.py
+++ b/pandas/plotting/_matplotlib/misc.py
@@ -64,6 +64,9 @@ def scatter_matrix(
     df = frame._get_numeric_data()
     n = df.columns.size
     naxes = n * n
+    
+    if diagonal not in ['hist', 'kde', None]:
+        raise ValueError(f"diagonal must be 'hist', 'kde', or None, got {diagonal!r}")
 
     fig, axes = create_subplots(naxes=naxes, figsize=figsize, ax=ax, squeeze=False)
```