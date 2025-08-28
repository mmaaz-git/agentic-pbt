# Bug Report: scipy.interpolate.RBFInterpolator Fails to Interpolate at Training Points

**Target**: `scipy.interpolate.RBFInterpolator`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

RBFInterpolator fails to pass through training points when given nearly colinear data, producing large errors (>1.3) instead of exact interpolation at the training points.

## Property-Based Test

```python
@given(
    n_points=st.integers(min_value=3, max_value=10),
    data_gen=st.data()
)
@settings(max_examples=30)
def test_rbf_interpolator(n_points, data_gen):
    points = data_gen.draw(st.lists(
        st.tuples(
            st.floats(min_value=-5, max_value=5, allow_nan=False),
            st.floats(min_value=-5, max_value=5, allow_nan=False)
        ),
        min_size=n_points, max_size=n_points, unique=True
    ))
    points = np.array(points)
    
    values = data_gen.draw(st.lists(
        st.floats(min_value=-10, max_value=10, allow_nan=False),
        min_size=n_points, max_size=n_points
    ))
    values = np.array(values)
    
    rbf = interpolate.RBFInterpolator(points, values.reshape(-1, 1))
    result = rbf(points).flatten()
    
    assert np.allclose(result, values, rtol=1e-5, atol=1e-5), \
        "RBFInterpolator doesn't pass through points accurately"
```

**Failing input**: 
```python
points = [(0.0, 2.0), (0.0, 1.5), (0.0, 2.2250738585e-313), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)]
values = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
```

## Reproducing the Bug

```python
import numpy as np
from scipy import interpolate

points = np.array([
    [0.0, 2.0],
    [0.0, 1.5],
    [0.0, 2.2250738585e-313],
    [0.0, 1.0],
    [0.0, 0.0],
    [1.0, 0.0]
])
values = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0])

rbf = interpolate.RBFInterpolator(points, values.reshape(-1, 1))
result = rbf(points).flatten()

print("Expected:", values)
print("Got:     ", result)
print("Max error:", np.max(np.abs(result - values)))
```

Output:
```
Expected: [0. 0. 0. 0. 0. 1.]
Got:      [-1.33826508 -0.19850581 -0.43570792 -1.01664084 -0.43570792  1.        ]
Max error: 1.338265078675578
```

## Why This Is A Bug

The RBFInterpolator documentation explicitly states: "The interpolant perfectly fits the data when [smoothing] is set to 0." Since the default smoothing parameter is 0, the interpolator should pass through all training points exactly. However, when given nearly colinear points (5 points with x=0 and 1 point with x=1), the interpolator produces large errors at the training points themselves, with errors exceeding 1.3 instead of the expected 0.

This violates the fundamental property of interpolation - that the interpolant must pass through the given data points when no smoothing is applied.

## Fix

The issue appears to be related to numerical instability when handling nearly colinear or degenerate point configurations. The fix would likely involve:

1. Better conditioning of the RBF matrix when points are nearly colinear
2. Adding regularization or using a more stable solver for ill-conditioned systems
3. Potentially warning users when the point configuration leads to poor conditioning

The exact fix would require examining the RBF matrix construction and solving code to improve numerical stability for edge cases.