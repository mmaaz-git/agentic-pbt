# Bug Report: scipy.ndimage.gaussian_filter1d ZeroDivisionError with sigma=0

**Target**: `scipy.ndimage.gaussian_filter1d`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`scipy.ndimage.gaussian_filter1d` raises `ZeroDivisionError` when called with `sigma=0`, while the multi-dimensional `gaussian_filter` handles this case correctly.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import numpy as np
import scipy.ndimage as ndi

@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False),
                min_size=1, max_size=10))
@settings(max_examples=100)
def test_gaussian_filter_zero_sigma(data):
    """gaussian_filter1d with sigma=0 should handle gracefully"""
    arr = np.array(data)
    result = ndi.gaussian_filter1d(arr, sigma=0)
    # With sigma=0, should return original array (no blurring)
    assert np.allclose(arr, result)
```

**Failing input**: Any array, e.g., `[1.0]`

## Reproducing the Bug

```python
import numpy as np
import scipy.ndimage as ndi

arr = np.array([1.0, 2.0, 3.0])
result = ndi.gaussian_filter1d(arr, sigma=0)
```

## Why This Is A Bug

1. **Inconsistent behavior**: `gaussian_filter` (multi-dimensional) correctly handles `sigma=0` by returning the original array, but `gaussian_filter1d` crashes with `ZeroDivisionError`.

2. **Mathematical interpretation**: `sigma=0` represents no blurring/smoothing, which is a valid edge case that should return the input unchanged.

3. **Poor error handling**: If `sigma=0` is considered invalid, the function should raise a descriptive `ValueError` rather than allowing a `ZeroDivisionError` to propagate.

## Fix

The issue occurs in `_gaussian_kernel1d` function where division by `sigma2 = sigma * sigma` happens without checking for zero. The fix should either:

1. Return the input array unchanged when sigma=0 (matching `gaussian_filter` behavior), or
2. Raise a clear ValueError if sigma must be positive

```diff
def gaussian_filter1d(input, sigma, axis=-1, order=0, output=None,
                      mode="reflect", cval=0.0, truncate=4.0, *, radius=None):
+    if sigma == 0:
+        # No blurring with sigma=0, return input unchanged
+        return input if output is None else np.copyto(output, input)
    
    # ... rest of the function
```