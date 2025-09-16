# Bug Report: pandas.Interval Zero-Width Interval Contains Bug

**Target**: `pandas.Interval` and `pandas.arrays.IntervalArray`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Zero-width intervals (where left == right) incorrectly report that they don't contain their endpoint when closed='left' or closed='right', violating the mathematical definition of closed intervals.

## Property-Based Test

```python
import pandas as pd
from hypothesis import given, strategies as st

@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_zero_width_interval_contains_bug(point):
    # Right-closed zero-width interval should contain its right endpoint
    interval_right = pd.Interval(point, point, closed='right')
    assert point in interval_right, \
        f"Right-closed interval {interval_right} should contain its right endpoint {point}"
    
    # Left-closed zero-width interval should contain its left endpoint
    interval_left = pd.Interval(point, point, closed='left')
    assert point in interval_left, \
        f"Left-closed interval {interval_left} should contain its left endpoint {point}"
```

**Failing input**: `point=0.0` (or any float value)

## Reproducing the Bug

```python
import pandas as pd

# Right-closed zero-width interval
interval_right = pd.Interval(0.0, 0.0, closed='right')
print(f"Interval: {interval_right}")  # Output: (0.0, 0.0]
print(f"0.0 in interval: {0.0 in interval_right}")  # Output: False
# Expected: True (right endpoint should be included in right-closed interval)

# Left-closed zero-width interval
interval_left = pd.Interval(0.0, 0.0, closed='left')
print(f"Interval: {interval_left}")  # Output: [0.0, 0.0)
print(f"0.0 in interval: {0.0 in interval_left}")  # Output: False
# Expected: True (left endpoint should be included in left-closed interval)

# Both-closed works correctly
interval_both = pd.Interval(0.0, 0.0, closed='both')
print(f"0.0 in interval_both: {0.0 in interval_both}")  # Output: True (Correct!)

# Neither-closed works correctly
interval_neither = pd.Interval(0.0, 0.0, closed='neither')
print(f"0.0 in interval_neither: {0.0 in interval_neither}")  # Output: False (Correct!)
```

## Why This Is A Bug

Mathematically, a closed interval includes its endpoints:
- A right-closed interval `(a, b]` includes point `b`
- A left-closed interval `[a, b)` includes point `a`
- When `a == b` (zero-width interval), the interval degenerates to a single point

For zero-width intervals:
- `(p, p]` should contain `p` (right endpoint is included)
- `[p, p)` should contain `p` (left endpoint is included)
- `[p, p]` should contain `p` (both endpoints are included) - this works correctly
- `(p, p)` should not contain `p` (neither endpoint is included) - this works correctly

The current implementation incorrectly returns `False` for left-closed and right-closed zero-width intervals, violating the mathematical definition of closed intervals.

## Fix

The bug likely lies in the interval containment logic that checks `left < x < right` or `left <= x <= right` without properly handling the degenerate case where `left == right`. The fix would need to special-case zero-width intervals:

```diff
# Pseudocode for the fix in __contains__ method
def __contains__(self, key):
    if self.left == self.right:  # Zero-width interval
        if self.closed == 'both':
            return key == self.left
        elif self.closed == 'left':
            return key == self.left  # Should contain left endpoint
        elif self.closed == 'right':
            return key == self.right  # Should contain right endpoint
        else:  # 'neither'
            return False
    else:
        # Regular interval logic...
```