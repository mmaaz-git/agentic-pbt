# Bug Report: scipy.differentiate API Inconsistency in Hessian Function

**Target**: `scipy.differentiate.hessian`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `hessian` function returns a result object with attribute `ddf` for the Hessian matrix, while `derivative` and `jacobian` return result objects with attribute `df` for their respective results. This creates an inconsistent API across the module's differentiation functions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from scipy import differentiate
import numpy as np

@given(
    x0=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    x1=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)
)
def test_api_consistency(x0, x1):
    """Test that all differentiation functions use consistent attribute names."""
    # Test derivative
    res_d = differentiate.derivative(lambda x: x**2, x0)
    assert hasattr(res_d, 'df'), "derivative should have 'df' attribute"
    
    # Test jacobian
    res_j = differentiate.jacobian(lambda x: np.array([x[0]**2]), np.array([x0]))
    assert hasattr(res_j, 'df'), "jacobian should have 'df' attribute"
    
    # Test hessian - FAILS: has 'ddf' instead of 'df'
    res_h = differentiate.hessian(lambda x: x[0]**2 + x[1]**2, np.array([x0, x1]))
    assert hasattr(res_h, 'df'), "hessian should have 'df' attribute for consistency"
```

**Failing input**: Any valid input fails the consistency check

## Reproducing the Bug

```python
import numpy as np
from scipy import differentiate

# Define test functions
def f_scalar(x):
    return x**2

def f_vector(x):
    return np.array([x[0]**2, x[1]**2])

def f_multivar(x):
    return x[0]**2 + x[1]**2

# Test each function
x_scalar = 1.0
x_vector = np.array([1.0, 2.0])

# derivative returns 'df'
res_d = differentiate.derivative(f_scalar, x_scalar)
print("derivative has 'df':", hasattr(res_d, 'df'))  # True

# jacobian returns 'df'
res_j = differentiate.jacobian(f_vector, x_vector)
print("jacobian has 'df':", hasattr(res_j, 'df'))    # True

# hessian returns 'ddf' instead
res_h = differentiate.hessian(f_multivar, x_vector)
print("hessian has 'df':", hasattr(res_h, 'df'))     # False
print("hessian has 'ddf':", hasattr(res_h, 'ddf'))   # True
```

## Why This Is A Bug

This violates the principle of API consistency within a module. Users expect similar functions to have similar interfaces. The inconsistency means:

1. Code that generically processes results from differentiation functions will fail for `hessian`
2. Users must remember different attribute names for essentially the same concept (the computed derivative)
3. The documentation at line 1036 of `_differentiate.py` incorrectly refers to "attribute `dff`" when it should be `ddf`, adding further confusion

## Fix

The fix would involve updating the `hessian` function to use `df` instead of `ddf` for consistency, or documenting a clear rationale for the difference. Additionally, the documentation typo should be corrected.

```diff
--- a/scipy/differentiate/_differentiate.py
+++ b/scipy/differentiate/_differentiate.py
@@ -1033,7 +1033,7 @@ def hessian(f, x, *, tolerances=None, maxiter=10, order=8, initial_step=0.5,
       the function at several abscissae in a single call.
     - argument `f` must return an array of shape ``(...)``.
-    - attribute ``dff`` of the result object will be an array of shape ``(m, m)``,
+    - attribute ``ddf`` of the result object will be an array of shape ``(m, m)``,
       the Hessian.

# And ideally, change the attribute name for consistency:
@@ -1001,7 +1001,7 @@ def hessian(f, x, *, tolerances=None, maxiter=10, order=8, initial_step=0.5,
             - ``-2`` : The maximum number of iterations was reached.
             - ``-3`` : A non-finite value was encountered.
 
-        ddf : float array
+        df : float array
             The Hessian of `f` at `x`, if the algorithm terminated
             successfully.
```