# Bug Report: scipy.integrate.cumulative_simpson Non-Monotonic for Non-Negative Functions

**Target**: `scipy.integrate.cumulative_simpson`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Cumulative Simpson integration produces non-monotonic results for non-negative functions, including negative values when integrating strictly positive functions.

## Property-Based Test

```python
@given(x=x_arrays(min_size=4))
@settings(max_examples=500)
def test_cumulative_monotonicity_nonnegative(x):
    y = np.abs(np.random.randn(len(x)))  # Non-negative values
    
    cum_simp = integrate.cumulative_simpson(y, x=x, initial=0)
    
    assert all(cum_simp[i] <= cum_simp[i+1] for i in range(len(cum_simp)-1)), \
        f"Simpson cumulative not monotonic for non-negative function"
```

**Failing input**: `x=array([0.0, 0.125, 1.0, 2.0])`

## Reproducing the Bug

```python
import numpy as np
import scipy.integrate as integrate

x = np.array([0.0, 0.125, 1.0, 2.0])
y = np.array([0.49671415, 0.1382643, 0.64768854, 1.52302986])

cum_simp = integrate.cumulative_simpson(y, x=x, initial=0)
print(f"Cumulative Simpson: {cum_simp}")
# Output: [ 0.          0.03856317 -0.00276498  1.05653714]

# Note: cum_simp[2] < 0 and cum_simp[2] < cum_simp[1], violating monotonicity
```

## Why This Is A Bug

For non-negative functions, the cumulative integral must be monotonically non-decreasing since we're always adding non-negative areas. Getting negative values when integrating positive functions violates fundamental properties of integration. This could lead to incorrect results in applications that depend on cumulative distribution functions or running totals.

## Fix

The issue likely stems from Simpson's rule requiring special handling at boundaries or with non-uniform spacing. The implementation may be using inappropriate extrapolation that produces negative contributions. A potential fix would ensure each incremental area contribution is properly bounded:

```diff
# Conceptual fix in cumulative_simpson implementation
- cumulative[i] = cumulative[i-1] + simpson_increment
+ # Ensure increment respects sign of integrand for monotonicity
+ increment = simpson_increment
+ if all(y[relevant_indices] >= 0):
+     increment = max(0, increment)
+ cumulative[i] = cumulative[i-1] + increment
```