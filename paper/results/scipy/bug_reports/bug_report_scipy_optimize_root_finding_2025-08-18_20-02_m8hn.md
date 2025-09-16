# Bug Report: scipy.optimize Root Finding Methods Return Different Roots

**Target**: `scipy.optimize.bisect`, `scipy.optimize.brentq`, `scipy.optimize.brenth`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

When multiple roots exist within a bracketing interval, different root-finding methods (bisect, brentq, brenth) return different roots without documenting this behavior.

## Property-Based Test

```python
@given(
    coeffs=polynomial_coeffs,
    a=safe_floats,
    b=safe_floats
)
def test_root_finding_consistency(coeffs, a, b):
    def f(x):
        return sum(c * x**i for i, c in enumerate(coeffs))
    
    assume(a < b)
    fa, fb = f(a), f(b)
    assume(fa * fb < 0)
    
    root_bisect = opt.bisect(f, a, b, xtol=1e-10)
    root_brentq = opt.brentq(f, a, b, xtol=1e-10)
    root_brenth = opt.brenth(f, a, b, xtol=1e-10)
    
    assert math.isclose(root_bisect, root_brentq, rel_tol=1e-8, abs_tol=1e-10)
```

**Failing input**: `coeffs=[0.0, 1.0, 0.0, -2.0], a=-2.0, b=1.0`

## Reproducing the Bug

```python
import scipy.optimize as opt

def f(x):
    return x * (1 - 2*x**2)

a, b = -2.0, 1.0

root_bisect = opt.bisect(f, a, b)
root_brentq = opt.brentq(f, a, b)
root_brenth = opt.brenth(f, a, b)

print(f'bisect: {root_bisect}')  # -0.7071067812
print(f'brentq: {root_brentq}')  # 0.7071067812
print(f'brenth: {root_brenth}')  # 0.7071067812
```

## Why This Is A Bug

The documentation for these methods does not specify which root will be returned when multiple roots exist in the interval. Users expect these methods to be interchangeable for the same problem, but they return different valid roots. This violates the principle of least surprise and can lead to inconsistent results in applications that switch between methods.

## Fix

The documentation should be updated to specify the behavior when multiple roots exist in the interval. Each method should document its root selection strategy (e.g., "returns the root closest to a", "returns the first root found", etc.). Alternatively, the methods could be modified to use a consistent root selection strategy when multiple roots exist.