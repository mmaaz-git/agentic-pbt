# Bug Report: scipy.integrate.simpson Produces Huge Incorrect Results with Close X Values

**Target**: `scipy.integrate.simpson`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Simpson integration produces wildly incorrect results (orders of magnitude off) when x array contains values that are very close together, even when the function values are reasonable.

## Property-Based Test

```python
@given(
    base_x=st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=5, max_size=10, unique=True
    ),
    epsilon=st.floats(min_value=1e-10, max_value=1e-5)
)
@settings(max_examples=500)
def test_simpson_close_x_values(base_x, epsilon):
    x = sorted(base_x)
    if len(x) > 2:
        insert_idx = len(x) // 2
        x.insert(insert_idx + 1, x[insert_idx] + epsilon)
    
    x = np.array(x)
    y = np.random.randn(len(x))
    
    result = integrate.simpson(y, x)
    trap_result = integrate.trapezoid(y, x)
    
    if abs(trap_result) > 1e-10:
        ratio = abs(result / trap_result)
        assert 0.01 < ratio < 100, \
            f"Simpson ({result}) vastly different from trapezoid ({trap_result})"
```

**Failing input**: `base_x=[0.0, 1.0, 2.0, 3.0, 4.0], epsilon=7.631312885787234e-06`

## Reproducing the Bug

```python
import numpy as np
import scipy.integrate as integrate

x = np.array([0.0, 1.0, 2.0, 2.0000076313128856, 3.0, 4.0])
y = np.array([0.49671415, -0.1382643, 0.64768854, 1.52302986, -0.23415337, -0.23413696])

simpson_result = integrate.simpson(y, x)
trapezoid_result = integrate.trapezoid(y, x)

print(f"Simpson: {simpson_result}")     # Output: 19117.632141019796
print(f"Trapezoid: {trapezoid_result}") # Output: 0.8442334841966406
print(f"Ratio: {simpson_result/trapezoid_result:.0f}x")  # Output: 22645x
```

## Why This Is A Bug

Simpson's rule should provide similar or better accuracy than the trapezoidal rule for smooth functions. Getting results that are 22,000 times larger indicates severe numerical instability. This makes Simpson integration unreliable for real-world data where x values might be close due to measurement precision or rounding.

## Fix

The issue appears when Simpson's formula divides by very small interval differences. The implementation needs robust handling of near-duplicate x values:

```diff
# Conceptual fix for handling close x values
+ # Detect and merge points that are too close
+ min_spacing = np.finfo(float).eps * max(abs(x.max()), abs(x.min()))
+ for i in range(len(x)-1):
+     if abs(x[i+1] - x[i]) < min_spacing:
+         # Merge points or use trapezoidal rule for this segment
+         return trapezoid_fallback(y, x)
```

Alternatively, implement adaptive switching to trapezoidal rule when numerical issues are detected.