# Bug Report: scipy.sparse.hstack Crashes on Empty List

**Target**: `scipy.sparse.hstack`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`scipy.sparse.hstack([])` crashes with an IndexError instead of raising a meaningful error message or returning an empty matrix.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import scipy.sparse as sp

@given(
    n_matrices=st.integers(min_value=0, max_value=5),
    rows=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_hstack_with_empty_list(n_matrices, rows, cols):
    """Test hstack with various list sizes including empty."""
    if n_matrices == 0:
        result = sp.hstack([])  # This crashes
        assert result.shape[0] >= 0  # Should handle gracefully
    else:
        matrices = [sp.random(rows, cols, density=0.5, format='csr') for _ in range(n_matrices)]
        result = sp.hstack(matrices)
        assert result.shape == (rows, cols * n_matrices)
```

**Failing input**: `n_matrices=0, rows=1, cols=1`

## Reproducing the Bug

```python
import scipy.sparse as sp

result = sp.hstack([])
```

## Why This Is A Bug

The function crashes with an unhelpful IndexError instead of:
1. Raising a clear ValueError like numpy does: "need at least one array to concatenate"
2. Returning a meaningful empty result

numpy.hstack([]) properly raises: `ValueError: need at least one array to concatenate`
scipy.sparse.vstack([]) properly raises: `ValueError: blocks must be 2-D`
scipy.sparse.hstack([]) crashes with: `IndexError: index 0 is out of bounds for axis 1 with size 0`

This violates the principle of failing gracefully with informative error messages.

## Fix

```diff
--- a/scipy/sparse/_construct.py
+++ b/scipy/sparse/_construct.py
@@ -797,6 +797,9 @@ def hstack(blocks, format=None, dtype=None):
            [3, 4, 6]])
     
     """
+    if len(blocks) == 0:
+        raise ValueError("need at least one array to concatenate")
+    
     return _block([blocks], format, dtype, return_spmatrix=True)
```