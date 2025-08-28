# Bug Report: scipy.fft DCT/IDCT Type 1 Fails on Single-Element Arrays

**Target**: `scipy.fft.dct` and `scipy.fft.idct` with `type=1`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

DCT and IDCT type 1 transforms crash with `RuntimeError: zero-length FFT requested` when given single-element arrays, while DST/IDST type 1 and all other transform types handle single-element arrays correctly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np
import scipy.fft

@given(st.floats(allow_nan=False, allow_infinity=False), 
       st.sampled_from([1, 2, 3, 4]))
def test_single_element_transforms(value, transform_type):
    x = np.array([value])
    
    # All transform types should handle single-element arrays consistently
    dct_result = scipy.fft.dct(x, type=transform_type)
    idct_result = scipy.fft.idct(x, type=transform_type)
    dst_result = scipy.fft.dst(x, type=transform_type)
    idst_result = scipy.fft.idst(x, type=transform_type)
    
    assert dct_result.shape == x.shape
    assert idct_result.shape == x.shape
    assert dst_result.shape == x.shape
    assert idst_result.shape == x.shape
```

**Failing input**: `x=array([0.])`, `transform_type=1`

## Reproducing the Bug

```python
import numpy as np
import scipy.fft

x = np.array([1.0])

result_dct = scipy.fft.dct(x, type=1)

result_idct = scipy.fft.idct(x, type=1)

result_dst = scipy.fft.dst(x, type=1)
print(f"DST type 1 works: {result_dst}")

result_idst = scipy.fft.idst(x, type=1)
print(f"IDST type 1 works: {result_idst}")

for t in [2, 3, 4]:
    scipy.fft.dct(x, type=t)
    scipy.fft.idct(x, type=t)
    print(f"DCT/IDCT type {t} works correctly")
```

## Why This Is A Bug

This violates the principle of API consistency. All cosine and sine transforms should handle edge cases uniformly. The fact that:
- DST/IDST type 1 work with single-element arrays
- DCT/IDCT types 2, 3, 4 work with single-element arrays
- Only DCT/IDCT type 1 fail

indicates an inconsistent implementation that breaks user expectations and makes the API harder to use reliably.

## Fix

The issue likely stems from the mathematical definition of DCT-I which involves indices that become invalid for N=1. The fix should either special-case single-element arrays or validate input size with a clearer error message.

```diff
# In scipy/fft/_pocketfft/realtransforms.py or similar location
def dct(x, type=2, ...):
    if type == 1:
+       if x.size == 1:
+           # DCT-I of single element is just the element itself
+           return x.copy()
        # existing DCT-I implementation
    ...

def idct(x, type=2, ...):
    if type == 1:
+       if x.size == 1:
+           # IDCT-I of single element is just the element itself
+           return x.copy()
        # existing IDCT-I implementation
    ...
```