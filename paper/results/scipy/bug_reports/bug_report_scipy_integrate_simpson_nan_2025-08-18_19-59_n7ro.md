# Bug Report: scipy.integrate.simpson Returns NaN with Very Small X Spacing

**Target**: `scipy.integrate.simpson`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Simpson integration returns NaN when x values contain extremely small spacing (e.g., 2.22e-309), even for simple functions like constant zero.

## Property-Based Test

```python
@given(x=x_arrays(), y=st.data())
@settings(max_examples=1000)
def test_cumulative_consistency_simpson(x, y):
    y_vals = y.draw(y_arrays(len(x)))
    
    total = integrate.simpson(y_vals, x)
    cumulative = integrate.cumulative_simpson(y_vals, x=x, initial=0)
    
    assert math.isclose(total, cumulative[-1], rel_tol=1e-10, abs_tol=1e-10), \
        f"Simpson: total={total}, cumulative[-1]={cumulative[-1]}"
```

**Failing input**: `x=array([0.00000000e+000, 2.22507386e-309, 1.00000000e+000]), y=array([0.0, 0.0, 0.0])`

## Reproducing the Bug

```python
import numpy as np
import scipy.integrate as integrate

x = np.array([0.00000000e+000, 2.22507386e-309, 1.00000000e+000])
y = np.array([0.0, 0.0, 0.0])

result = integrate.simpson(y, x)
print(f"Simpson result: {result}")  # Output: nan

trap_result = integrate.trapezoid(y, x)
print(f"Trapezoid result: {trap_result}")  # Output: 0.0
```

## Why This Is A Bug

The integral of y=0 over any interval should be 0, not NaN. The function should handle numerical edge cases gracefully. Trapezoid integration correctly returns 0 for the same input, showing this is a Simpson-specific issue. The overflow warnings suggest division by very small numbers causing numerical instability.

## Fix

The issue appears to be in the Simpson formula implementation when computing ratios of very small intervals. The fix would involve adding numerical safeguards:

```diff
# In scipy/integrate/_quadrature.py, around line 367-369
- h0divh1 = np.true_divide(h0, h1, out=np.zeros_like(h0), where=h1 != 0)
+ # Add minimum threshold to prevent overflow
+ h1_safe = np.where(np.abs(h1) < 1e-200, 1e-200, h1)
+ h0divh1 = np.true_divide(h0, h1_safe, out=np.zeros_like(h0), where=h1_safe != 0)
```

A more robust fix would involve checking for degenerate intervals and falling back to simpler methods when numerical issues are detected.