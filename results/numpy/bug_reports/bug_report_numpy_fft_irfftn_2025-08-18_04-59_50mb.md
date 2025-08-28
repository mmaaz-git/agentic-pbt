# Bug Report: numpy.fft.irfftn Fails on Single-Element Arrays

**Target**: `numpy.fft.irfftn`, `numpy.fft.irfft`, `numpy.fft.irfft2`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The inverse real FFT functions (`irfftn`, `irfft`, `irfft2`) crash with a ValueError when attempting to invert the FFT of single-element real arrays, violating the round-trip property that `irfftn(rfftn(x)) ≈ x`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np

@given(st.lists(st.floats(-1e6, 1e6, allow_nan=False, allow_infinity=False), 
                min_size=1, max_size=1))
def test_rfft_irfft_round_trip_single_element(x):
    x = np.array(x)
    result = np.fft.irfftn(np.fft.rfftn(x))
    assert np.allclose(result, x, rtol=1e-10, atol=1e-10)
```

**Failing input**: `[1.0]` (or any single-element array)

## Reproducing the Bug

```python
import numpy as np

x = np.array([1.0])
rfft_result = np.fft.rfftn(x)
print(f"rfftn([1.0]) = {rfft_result}")

irfft_result = np.fft.irfftn(rfft_result)
```

This raises:
```
ValueError: Invalid number of FFT data points (0) specified.
```

## Why This Is A Bug

The FFT round-trip property should hold for all valid inputs. Single-element arrays are valid inputs to `rfftn`, which successfully produces a single-element complex array. However, the corresponding inverse function `irfftn` fails to handle this case, incorrectly calculating the output size as 0 instead of 1.

The bug occurs in the shape calculation logic within `_cook_nd_args` function in `/numpy/fft/_pocketfft.py`. When `invreal=1`, it uses the formula `s[-1] = (a.shape[axes[-1]] - 1) * 2` which evaluates to 0 for single-element inputs.

## Fix

The shape calculation in `_cook_nd_args` needs to handle the edge case of single-element FFT results. The inverse real FFT of a single-element complex array should produce a single-element real array.

```diff
--- a/numpy/fft/_pocketfft.py
+++ b/numpy/fft/_pocketfft.py
@@ -105,7 +105,10 @@ def _cook_nd_args(a, s=None, axes=None, invreal=0):
     if len(s) != len(axes):
         raise ValueError("Shape and axes have different lengths.")
     if invreal and shapeless:
-        s[-1] = (a.shape[axes[-1]] - 1) * 2
+        # Handle single-element case for inverse real FFT
+        if a.shape[axes[-1]] == 1:
+            s[-1] = 1
+        else:
+            s[-1] = (a.shape[axes[-1]] - 1) * 2
     if None in s:
         msg = ("Passing an array containing `None` values to `s` is "
```