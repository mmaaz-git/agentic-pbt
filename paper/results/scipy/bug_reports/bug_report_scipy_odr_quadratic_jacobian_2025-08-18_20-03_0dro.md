# Bug Report: scipy.odr Quadratic Model Jacobian Wrong Shape for Single Data Point

**Target**: `scipy.odr.quadratic.fjacb`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The jacobian function `fjacb` of scipy.odr's quadratic model returns an incorrectly shaped array when given a single data point, returning (n_params, 1) instead of the expected (1, n_params).

## Property-Based Test

```python
@given(
    beta=st.lists(small_floats, min_size=2, max_size=4),
    x=st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
    h=st.floats(min_value=1e-8, max_value=1e-6)
)
def test_jacobian_consistency(beta, x, h):
    """Test that analytical jacobians match numerical differentiation"""
    beta = np.array(beta)
    x_arr = np.array([x])
    
    # Test quadratic model jacobians
    if len(beta) >= 3:
        beta_quad = beta[:3]
        
        # Analytical jacobian
        analytical_jac = odr.quadratic.fjacb(beta_quad, x_arr)
        
        # Numerical jacobian
        numerical_jac = np.zeros_like(analytical_jac)
        for i in range(3):
            beta_plus = beta_quad.copy()
            beta_minus = beta_quad.copy()
            beta_plus[i] += h
            beta_minus[i] -= h
            
            f_plus = odr.quadratic.fcn(beta_plus, x_arr)
            f_minus = odr.quadratic.fcn(beta_minus, x_arr)
            numerical_jac[:, i] = (f_plus - f_minus) / (2 * h)
        
        # Check they're close
        assert np.allclose(analytical_jac, numerical_jac, rtol=1e-4, atol=1e-6)
```

**Failing input**: `beta=[0.0, 0.0, 0.0], x=0.0, h=9.835783115670487e-07`

## Reproducing the Bug

```python
import numpy as np
import scipy.odr as odr

beta = np.array([0.0, 0.0, 0.0])
x_arr = np.array([0.0])

# Get jacobian for single data point
jac = odr.quadratic.fjacb(beta, x_arr)

print(f"Input x shape: {x_arr.shape}")
print(f"Jacobian shape: {jac.shape}")
print(f"Expected shape: (1, 3)")
print(f"Bug: Jacobian has shape {jac.shape} instead of (1, 3)")

# This causes indexing errors
try:
    for i in range(3):
        print(f"Column {i}: {jac[:, i]}")
except IndexError as e:
    print(f"IndexError when accessing columns: {e}")
```

## Why This Is A Bug

The jacobian of a function with respect to parameters should have shape (n_data_points, n_parameters). For 1 data point and 3 parameters (quadratic has 3 coefficients), the shape should be (1, 3). However, the function returns (3, 1), which is transposed. This violates the expected interface for jacobian functions and causes indexing errors in downstream code that expects the standard shape.

## Fix

The jacobian function likely has the dimensions swapped. The fix would involve ensuring the returned array has the correct shape:

```diff
def fjacb_quadratic(beta, x):
    # ... existing implementation ...
-   return jacobian  # Current: returns (n_params, n_data) when n_data=1
+   if x.ndim == 0 or (x.ndim == 1 and len(x) == 1):
+       return jacobian.T  # Transpose to get (n_data, n_params)
+   return jacobian
```