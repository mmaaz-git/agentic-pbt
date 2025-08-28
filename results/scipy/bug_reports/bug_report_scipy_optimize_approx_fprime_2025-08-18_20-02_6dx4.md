# Bug Report: scipy.optimize.approx_fprime Fails for Small Magnitude Inputs

**Target**: `scipy.optimize.approx_fprime`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `approx_fprime` function produces incorrect gradient approximations for small-magnitude inputs due to inappropriate default epsilon, causing up to 7450% relative error.

## Property-Based Test

```python
@given(
    x=st.lists(safe_floats, min_size=1, max_size=5),
    epsilon=st.floats(min_value=1e-10, max_value=1e-5)
)
def test_approx_fprime_polynomial(x, epsilon):
    x = np.array(x)
    
    def f(x):
        return np.sum(x**2)
    
    def true_grad(x):
        return 2 * x
    
    approx_grad = opt.approx_fprime(x, f, epsilon)
    true_gradient = true_grad(x)
    
    tol = max(epsilon * 100, 1e-6)
    assert np.allclose(approx_grad, true_gradient, rtol=tol, atol=tol)
```

**Failing input**: `x=[1.192092896e-07], epsilon=default`

## Reproducing the Bug

```python
import scipy.optimize as opt
import numpy as np

def f(x):
    return x**2

test_values = [1e-7, 1e-8, 1e-9, 1e-10]

for val in test_values:
    x = np.array([val])
    approx_grad = opt.approx_fprime(x, f)
    true_grad = 2 * x
    rel_error = abs((approx_grad - true_grad) / true_grad)
    
    print(f'x={val:e}: relative error = {rel_error[0]:.1%}')
```

Output:
```
x=1.000000e-07: relative error = 7.5%
x=1.000000e-08: relative error = 74.5%
x=1.000000e-09: relative error = 745.1%
x=1.000000e-10: relative error = 7450.6%
```

## Why This Is A Bug

The default epsilon (≈1.49e-8) is too large relative to small input values. When x < sqrt(epsilon), the finite difference (f(x+ε) - f(x))/ε is dominated by ε rather than x, causing massive relative errors. This makes the function unreliable for optimization problems involving small-magnitude variables.

## Fix

```diff
def approx_fprime(xk, f, epsilon=None, *args):
+   if epsilon is None:
+       # Scale epsilon based on magnitude of xk
+       epsilon = np.sqrt(np.finfo(float).eps) * np.maximum(1.0, np.abs(xk))
    # ... rest of function
```

The epsilon should be scaled relative to the magnitude of the input values to maintain consistent relative accuracy across different scales.