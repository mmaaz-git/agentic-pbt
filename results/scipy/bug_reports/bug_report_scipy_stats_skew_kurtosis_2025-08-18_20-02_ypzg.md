# Bug Report: scipy.stats.skew and scipy.stats.kurtosis Return NaN for Constant Arrays

**Target**: `scipy.stats.skew` and `scipy.stats.kurtosis`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `skew` and `kurtosis` functions return NaN when given constant arrays (arrays where all values are the same), when they should return 0 for skewness and a defined value for kurtosis.

## Property-Based Test

```python
import numpy as np
import scipy.stats as ss
from hypothesis import given, strategies as st


@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
       st.integers(min_value=2, max_value=100))
def test_skew_constant_array_should_be_zero(value, size):
    """Skewness of a constant array should be 0, not NaN"""
    arr = np.full(size, value)
    skewness = ss.skew(arr)
    assert not np.isnan(skewness), f"skew returned NaN for constant array of {value}"
```

**Failing input**: `value=0.0, size=2`

## Reproducing the Bug

```python
import numpy as np
import scipy.stats as ss

# Test with various constant arrays
const_zeros = np.array([0.0, 0.0, 0.0])
const_fives = np.array([5.0, 5.0, 5.0])

print("Zeros array skewness:", ss.skew(const_zeros))
print("Fives array skewness:", ss.skew(const_fives))
print("Zeros array kurtosis:", ss.kurtosis(const_zeros))
print("Fives array kurtosis:", ss.kurtosis(const_fives))
```

Output:
```
Zeros array skewness: nan
Fives array skewness: nan
Zeros array kurtosis: nan
Fives array kurtosis: nan
```

## Why This Is A Bug

A constant distribution has zero skewness by definition - there is no asymmetry when all values are identical. The skewness formula involves dividing by the standard deviation, which is zero for constant arrays, leading to a 0/0 indeterminate form. However, the mathematically correct result is 0 for skewness (no asymmetry) and -3 for excess kurtosis (or 0 for raw kurtosis) for a degenerate distribution.

Returning NaN breaks downstream calculations and violates the mathematical properties of these statistics. Users would expect a sensible value (0 for skewness) rather than NaN, which requires special handling.

## Fix

The functions should check if the standard deviation is zero (or near-zero) and return the appropriate values for constant distributions:
- `skew`: return 0.0
- `kurtosis`: return -3.0 (for Fisher=True) or 0.0 (for Fisher=False)

```diff
def skew(a, axis=0, bias=True, nan_policy='propagate', *, keepdims=False):
    # ... existing code ...
    
    # After calculating standard deviation
+   if np.all(np.isclose(std_val, 0)):
+       # Constant distribution has zero skewness
+       return np.zeros_like(std_val)
    
    # ... rest of existing code ...
```