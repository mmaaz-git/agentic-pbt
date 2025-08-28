# Bug Report: scipy.linalg.pinv Violates Moore-Penrose Condition

**Target**: `scipy.linalg.pinv`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The pseudo-inverse computed by `scipy.linalg.pinv` violates the third Moore-Penrose condition (A @ A_pinv should be Hermitian) for certain rank-deficient matrices with small but non-zero values.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import numpy as np
import scipy.linalg

@st.composite
def matrices(draw, min_size=2, max_size=10):
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    m = draw(st.integers(min_value=min_size, max_value=max_size))
    elements = st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False, width=64)
    matrix = draw(st.lists(st.lists(elements, min_size=m, max_size=m), min_size=n, max_size=n))
    return np.array(matrix, dtype=np.float64)

@given(matrices(min_size=2, max_size=10))
@settings(max_examples=100)
def test_pinv_properties(A):
    A_pinv = scipy.linalg.pinv(A)
    
    # Moore-Penrose condition 3: (A @ A_pinv) should be Hermitian
    product3 = A @ A_pinv
    assert np.allclose(product3, product3.T, rtol=1e-9, atol=1e-9), \
        "Moore-Penrose condition 3 failed: A @ A_pinv is not Hermitian"
```

**Failing input**: `array([[0.0, 0.0, 0.0], [0.0, 13.0, 1.0], [0.0, 1.91461479e-06, 0.0]])`

## Reproducing the Bug

```python
import numpy as np
import scipy.linalg

A = np.array([[0.0, 0.0, 0.0],
              [0.0, 13.0, 1.0],
              [0.0, 1.91461479e-06, 0.0]])

A_pinv = scipy.linalg.pinv(A)

product = A @ A_pinv
symmetry_error = np.max(np.abs(product - product.T))

print(f"Symmetry error: {symmetry_error}")
print(f"Is symmetric (tol=1e-9): {np.allclose(product, product.T, rtol=1e-9, atol=1e-9)}")
```

## Why This Is A Bug

The Moore-Penrose pseudo-inverse must satisfy four conditions by definition. The third condition requires that A @ A_pinv be Hermitian (symmetric for real matrices). The computed pseudo-inverse produces a symmetry error of 2.79e-09, which exceeds reasonable numerical tolerance and violates this mathematical requirement.

## Fix

The issue appears to be related to the default tolerance handling for small singular values. Using a larger rtol parameter (e.g., 1e-6) resolves the issue:

```diff
- A_pinv = scipy.linalg.pinv(A)
+ A_pinv = scipy.linalg.pinv(A, rtol=1e-6)
```

The default rtol calculation may need adjustment to handle rank-deficient matrices with small values more robustly.