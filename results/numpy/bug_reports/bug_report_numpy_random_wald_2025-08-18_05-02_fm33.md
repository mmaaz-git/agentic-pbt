# Bug Report: numpy.random.wald Produces Negative Values

**Target**: `numpy.random.wald`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `numpy.random.wald` function produces negative values when called with large mean parameters (>= 1e8), violating the mathematical definition of the Wald (inverse Gaussian) distribution which only produces positive values.

## Property-Based Test

```python
import numpy.random
from hypothesis import given, strategies as st, settings

@given(
    st.floats(min_value=1e8, max_value=1e15),
    st.floats(min_value=0.1, max_value=10.0)
)
@settings(max_examples=50)
def test_wald_negative_values(mean, scale):
    """Wald distribution should never produce negative values"""
    samples = numpy.random.wald(mean, scale, size=1000)
    assert all(s >= 0 for s in samples), f"Found negative values with mean={mean}, scale={scale}"
```

**Failing input**: `mean=100000000.0, scale=1.099609375`

## Reproducing the Bug

```python
import numpy.random

numpy.random.seed(42)
mean = 1e8
scale = 1.0
samples = numpy.random.wald(mean, scale, size=1000)

negative_samples = samples[samples < 0]
print(f"Generated {len(samples)} samples")
print(f"Found {len(negative_samples)} negative values")
print(f"Minimum value: {samples.min()}")
```

## Why This Is A Bug

The Wald (inverse Gaussian) distribution is mathematically defined to only produce positive values. The probability density function is only defined for x > 0, and the documentation states that the function "Draw[s] samples from a Wald, or inverse Gaussian, distribution" with "mean : float or array_like of floats - Distribution mean, must be > 0". 

Negative values violate this fundamental property and can cause downstream issues in applications that rely on the mathematical properties of the distribution, such as reliability modeling, financial modeling, and statistical inference.

## Fix

The issue likely stems from numerical precision problems when computing the inverse transform or rejection sampling for large mean values. The implementation should include bounds checking to ensure all generated values are strictly positive, possibly by:

1. Adding explicit bounds checking after sample generation
2. Using a more numerically stable algorithm for large mean values
3. Switching to an alternative sampling method when mean exceeds a certain threshold

```diff
# Conceptual fix in the sampling routine
def wald_sample(mean, scale):
    # ... existing sampling logic ...
    sample = compute_sample(mean, scale)
+   # Ensure non-negativity due to numerical issues
+   if sample < 0:
+       sample = 0.0  # or resample
    return sample
```