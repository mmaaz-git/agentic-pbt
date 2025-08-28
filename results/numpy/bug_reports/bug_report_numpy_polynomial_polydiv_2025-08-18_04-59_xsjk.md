# Bug Report: numpy.polynomial.polynomial.polydiv Produces Infinity When Dividing Polynomial by Itself

**Target**: `numpy.polynomial.polynomial.polydiv`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`polydiv` incorrectly produces `-inf` in the remainder when dividing a polynomial with very small coefficients by itself, instead of returning the expected quotient of [1] and remainder of [0].

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy.polynomial.polynomial as poly
import numpy as np

nonzero_polynomial_coeffs = st.lists(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    min_size=1, max_size=10
).filter(lambda c: not all(abs(x) < 1e-10 for x in c))

@given(nonzero_polynomial_coeffs)
def test_polydiv_by_self(c):
    """Dividing polynomial by itself should give quotient [1] and remainder [0]"""
    q, r = poly.polydiv(c, c)
    
    q_trimmed = poly.polytrim(q, tol=1e-10)
    r_trimmed = poly.polytrim(r, tol=1e-10)
    
    assert np.allclose(q_trimmed, [1], rtol=1e-8, atol=1e-8)
    assert len(r_trimmed) == 0 or np.allclose(r_trimmed, [0], rtol=1e-8, atol=1e-8)
```

**Failing input**: `c=[1.0, 2.225073858507e-311]`

## Reproducing the Bug

```python
import numpy.polynomial.polynomial as poly
import numpy as np

c = [1.0, 2.225073858507e-311]
q, r = poly.polydiv(c, c)

print(f"Dividing {c} by itself")
print(f"Quotient: {q}")  
print(f"Remainder: {r}")  
print(f"Is remainder finite? {np.isfinite(r).all()}")
```

## Why This Is A Bug

Dividing any non-zero polynomial by itself should always yield a quotient of 1 and a remainder of 0, as this is a fundamental algebraic property. The function fails this mathematical invariant when dealing with coefficients near the limits of floating-point representation, producing `-inf` in the remainder due to numerical overflow during the division algorithm.

## Fix

The issue occurs in the polynomial division algorithm when normalizing very small coefficients. The fix would require adding numerical safeguards in the division routine to handle subnormal numbers:

```diff
--- a/numpy/polynomial/polynomial.py
+++ b/numpy/polynomial/polynomial.py
@@ -414,7 +414,10 @@ def polydiv(c1, c2):
     while i >= 0:
         q[i] = c1[lc1] / c2[lc2]
         scl = q[i]
-        c2 = c2[:-1] / scl
+        # Avoid overflow when dividing by very small numbers
+        with np.errstate(over='raise'):
+            c2_scaled = c2[:-1] / scl if abs(scl) > np.finfo(float).tiny else c2[:-1] * 0
+        c2 = c2_scaled
         c1[i:] -= scl * c2
         lc1 -= 1
         i -= 1
```