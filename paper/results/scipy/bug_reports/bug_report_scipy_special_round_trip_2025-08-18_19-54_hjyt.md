# Bug Report: scipy.special Round-Trip Functions Fail Catastrophically

**Target**: `scipy.special.expit/logit`, `scipy.special.erf/erfinv`, `scipy.special.erfc/erfcinv`, `scipy.stats.norm.cdf/ppf`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Multiple pairs of inverse functions in scipy fail their round-trip property for moderate input values, returning infinity instead of the original value when the forward function output rounds to its asymptotic limit in float64.

## Property-Based Test

```python
import scipy.special as sp
from hypothesis import given, strategies as st
import numpy as np

@given(st.floats(min_value=30, max_value=100))
def test_expit_logit_catastrophic_failure(x):
    """Test that logit(expit(x)) should return x, not inf"""
    y = sp.expit(x)
    x_recovered = sp.logit(y)
    assert np.isfinite(x_recovered), f"logit(expit({x})) returned {x_recovered}"

@given(st.floats(min_value=5.5, max_value=10))
def test_erf_erfinv_catastrophic_failure(x):
    """Test that erfinv(erf(x)) should return x, not inf"""
    y = sp.erf(x)
    x_recovered = sp.erfinv(y)
    assert np.isfinite(x_recovered), f"erfinv(erf({x})) returned {x_recovered}"
```

**Failing input**: Multiple values, e.g., `x=37.0` for expit/logit, `x=6.0` for erf/erfinv

## Reproducing the Bug

```python
import scipy.special as sp
import scipy.stats as stats

# Bug 1: expit/logit round-trip fails
x = 37.0
y = sp.expit(x)  # Returns 1.0 due to float64 rounding
x_recovered = sp.logit(y)  # Returns inf
print(f"logit(expit({x})) = {x_recovered}")  # inf instead of 37.0

# Bug 2: erf/erfinv round-trip fails  
x = 6.0
y = sp.erf(x)  # Returns 1.0 due to float64 rounding
x_recovered = sp.erfinv(y)  # Returns inf
print(f"erfinv(erf({x})) = {x_recovered}")  # inf instead of 6.0

# Bug 3: erfc/erfcinv round-trip fails
x = -6.0
y = sp.erfc(x)  # Returns 2.0 due to float64 rounding
x_recovered = sp.erfcinv(y)  # Returns -inf
print(f"erfcinv(erfc({x})) = {x_recovered}")  # -inf instead of -6.0

# Bug 4: norm.cdf/ppf round-trip fails
x = 9.0
p = stats.norm.cdf(x)  # Returns 1.0 due to float64 rounding
x_recovered = stats.norm.ppf(p)  # Returns inf
print(f"norm.ppf(norm.cdf({x})) = {x_recovered}")  # inf instead of 9.0
```

## Why This Is A Bug

The documentation explicitly states these are inverse functions:
- expit docstring: "It is the inverse of the logit function"
- erfinv/erfcinv are documented as inverse functions
- norm.ppf docstring: "Percent point function (inverse of `cdf`)"

Users reasonably expect round-trip operations to work for moderate values like x=37. While this stems from float64 precision limits, the functions could handle edge cases better rather than returning infinity.

## Fix

The functions could use specialized approximations near boundaries. For example:

```diff
# Conceptual fix for expit/logit:
def logit(p):
    if p == 1.0:
+       # Use Taylor expansion or return large finite value
+       return 36.7  # Or use higher precision computation
    elif p == 0.0:
+       return -36.7
    return np.log(p / (1 - p))

# Alternative: Keep track of log-space values
def log_expit(x):
    """Return log(expit(x)) without overflow"""
    return -np.logaddexp(0, -x)
```

A more robust solution would involve either:
1. Using extended precision near boundaries
2. Returning the largest representable finite value instead of infinity
3. Providing alternative functions that work in log-space for numerical stability
4. Warning users when precision loss occurs