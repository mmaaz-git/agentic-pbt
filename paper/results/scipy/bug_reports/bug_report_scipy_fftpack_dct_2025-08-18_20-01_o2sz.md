# Bug Report: scipy.fftpack DCT/IDCT Round-Trip Failure

**Target**: `scipy.fftpack.dct` and `scipy.fftpack.idct`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `idct` function with default normalization (norm=None) does not actually invert the `dct` function, despite being named "Inverse Discrete Cosine Transform". All DCT types (1-4) fail the round-trip property with default parameters.

## Property-Based Test

```python
import numpy as np
import scipy.fftpack
from hypothesis import given, strategies as st, settings

@st.composite
def float_arrays(draw, min_size=1, max_size=1000):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    elements = draw(st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=size, max_size=size
    ))
    return np.array(elements, dtype=np.float64)

@given(float_arrays(), st.sampled_from([1, 2, 3, 4]))
@settings(max_examples=100)
def test_dct_idct_round_trip(x, dct_type):
    """Test that idct(dct(x)) == x for all DCT types."""
    if dct_type == 1 and len(x) <= 1:
        return  # DCT type 1 requires length > 1
    
    dct_result = scipy.fftpack.dct(x, type=dct_type)
    round_trip = scipy.fftpack.idct(dct_result, type=dct_type)
    np.testing.assert_allclose(round_trip, x, rtol=1e-10, atol=1e-10)
```

**Failing input**: Any non-trivial array, e.g., `np.array([1.0, 2.0, 3.0, 4.0, 5.0])` with `dct_type=1`

## Reproducing the Bug

```python
import numpy as np
import scipy.fftpack

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

for dct_type in [1, 2, 3, 4]:
    dct_result = scipy.fftpack.dct(x, type=dct_type)
    idct_result = scipy.fftpack.idct(dct_result, type=dct_type)
    
    print(f'DCT Type {dct_type}:')
    print(f'  Original:     {x}')
    print(f'  After round-trip: {idct_result}')
    print(f'  Scale factor: {idct_result[0] / x[0]:.1f}')
```

Output:
```
DCT Type 1:
  Original:     [1. 2. 3. 4. 5.]
  After round-trip: [ 8. 16. 24. 32. 40.]
  Scale factor: 8.0
DCT Type 2:
  Original:     [1. 2. 3. 4. 5.]
  After round-trip: [10. 20. 30. 40. 50.]
  Scale factor: 10.0
DCT Type 3:
  Original:     [1. 2. 3. 4. 5.]
  After round-trip: [10. 20. 30. 40. 50.]
  Scale factor: 10.0
DCT Type 4:
  Original:     [1. 2. 3. 4. 5.]
  After round-trip: [10. 20. 30. 40. 50.]
  Scale factor: 10.0
```

## Why This Is A Bug

The function `scipy.fftpack.idct` is explicitly named "Inverse Discrete Cosine Transform" and its docstring states "Return the Inverse Discrete Cosine Transform of an arbitrary type sequence." Users reasonably expect that `idct(dct(x))` should return `x`, but this only works with `norm='ortho'`, not with the default `norm=None`. The default behavior applies an unexpected scaling factor (2N for types 2-4, 2(N-1) for type 1), violating the inverse relationship that the function name promises.

## Fix

The issue is a documentation/API design problem. Either:
1. The default normalization should be changed to make `idct` a true inverse of `dct`
2. The documentation should prominently warn that `norm='ortho'` is required for true inverse behavior

A documentation fix would look like:

```diff
-Return the Inverse Discrete Cosine Transform of an arbitrary type sequence.
+Return the Inverse Discrete Cosine Transform of an arbitrary type sequence.
+
+Warning
+-------
+With the default normalization (norm=None), this function does not compute
+a true inverse of dct(). The result will be scaled by a factor of 2N (or 
+2(N-1) for type 1). Use norm='ortho' for both dct() and idct() to get a 
+true inverse relationship where idct(dct(x)) == x.
```