# Bug Report: scipy.cluster.hierarchy.cophenet Returns NaN for Identical Observations

**Target**: `scipy.cluster.hierarchy.cophenet`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `cophenet` function returns NaN instead of a valid correlation coefficient when all input observations are identical, causing division by zero in the correlation calculation.

## Property-Based Test

```python
@given(observations(min_samples=4, max_samples=15, min_features=2, max_features=4))
def test_cophenet_bounds(obs):
    from scipy.spatial.distance import pdist
    
    Z = hier.linkage(obs, method='average')
    Y = pdist(obs)
    
    c, coph_dists = hier.cophenet(Z, Y)
    
    # Correlation coefficient should be between -1 and 1
    assert -1.0 <= c <= 1.0, f"Cophenetic correlation {c} outside [-1, 1]"
```

**Failing input**: `array([[0., 0.], [0., 0.], [0., 0.], [0., 0.]])`

## Reproducing the Bug

```python
import numpy as np
import scipy.cluster.hierarchy as hier
from scipy.spatial.distance import pdist

obs = np.array([[0., 0.],
                [0., 0.],
                [0., 0.],
                [0., 0.]])

Z = hier.linkage(obs, method='average')
Y = pdist(obs)

c, coph_dists = hier.cophenet(Z, Y)
print(f"Cophenetic correlation: {c}")
print(f"Is NaN? {np.isnan(c)}")
```

## Why This Is A Bug

The function should handle the edge case of identical observations gracefully. When all pairwise distances are zero (because all points are identical), the Pearson correlation calculation results in 0/0 = NaN. This violates the expected behavior that correlation coefficients should be in the range [-1, 1]. The function should either:

1. Return a defined value (e.g., 1.0 since the cophenetic distances perfectly match the original distances)
2. Raise an informative error explaining that correlation is undefined for zero-variance data
3. Document this behavior in the docstring

Currently, it silently returns NaN with only a RuntimeWarning, which can cause downstream issues in user code expecting valid correlation values.

## Fix

The issue could be fixed by adding a check for zero variance before computing the correlation:

```diff
--- a/scipy/cluster/hierarchy.py
+++ b/scipy/cluster/hierarchy.py
@@ -1710,6 +1710,11 @@ def cophenet(Z, Y=None):
     denomA = dmY - mY ** 2
     denomB = dmZ - mZ ** 2
     
+    # Handle zero variance case
+    if xp.sum(denomA) == 0 or xp.sum(denomB) == 0:
+        # When all distances are identical, return 1.0 if they match, else undefined
+        return (1.0 if xp.allclose(Ys, Zs) else xp.nan), Zs
+    
     numerator = (Ys - mY) * (Zs - mZ)
     
     c = xp.sum(numerator) / xp.sqrt(xp.sum(denomA) * xp.sum(denomB))
```

Alternatively, raise a more informative error when this condition is detected, similar to how `scipy.stats.pearsonr` handles constant input with a `ConstantInputWarning`.