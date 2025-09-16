# Bug Report: optax.linear_onecycle_schedule Division by Zero with Small Steps

**Target**: `optax.linear_onecycle_schedule`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`linear_onecycle_schedule` returns NaN for all step counts when `transition_steps=1` due to division by zero in the underlying `piecewise_interpolate_schedule` function.

## Property-Based Test

```python
@given(
    transition_steps=st.integers(min_value=1, max_value=100),
    peak_value=st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    pct_start=st.floats(min_value=0.01, max_value=0.49, allow_nan=False, allow_infinity=False),
    pct_final=st.floats(min_value=0.51, max_value=0.99, allow_nan=False, allow_infinity=False)
)
def test_linear_onecycle_phase_ordering(transition_steps, peak_value, pct_start, pct_final):
    assume(pct_start < pct_final)
    
    schedule = optax.linear_onecycle_schedule(
        transition_steps=transition_steps,
        peak_value=peak_value,
        pct_start=pct_start,
        pct_final=pct_final
    )
    
    peak_step = int(pct_start * transition_steps)
    result_at_peak = float(schedule(peak_step))
    assert abs(result_at_peak - peak_value) <= peak_value * 0.1
```

**Failing input**: `transition_steps=1, peak_value=1.0, pct_start=0.25, pct_final=0.75`

## Reproducing the Bug

```python
import optax
import numpy as np

schedule = optax.linear_onecycle_schedule(
    transition_steps=1,
    peak_value=1.0,
    pct_start=0.25,
    pct_final=0.75
)

result = schedule(0)
print(f"Result: {result}")
assert not np.isnan(result), "Result is NaN!"
```

## Why This Is A Bug

The function should handle edge cases gracefully and return valid numerical values for all valid inputs. When `transition_steps=1`, the schedule creates boundaries at steps [0, 0, 0, 1] which leads to zero-length intervals. The division `pct = (count - bounds[:-1]) / interval_sizes` in `piecewise_interpolate_schedule` (line 472) causes division by zero, resulting in NaN values.

## Fix

The issue is in `piecewise_interpolate_schedule` where it doesn't handle zero-length intervals. Here's a fix:

```diff
--- a/optax/schedules/_schedule.py
+++ b/optax/schedules/_schedule.py
@@ -469,7 +469,11 @@ def piecewise_interpolate_schedule(
 
   def schedule(count):
     indicator = (bounds[:-1] <= count) & (count < bounds[1:])
-    pct = (count - bounds[:-1]) / interval_sizes
+    # Handle zero-length intervals to avoid division by zero
+    with np.errstate(divide='ignore', invalid='ignore'):
+      pct = (count - bounds[:-1]) / interval_sizes
+      # Set pct to 1.0 for zero-length intervals (instantaneous transition)
+      pct = np.where(interval_sizes == 0, 1.0, pct)
     interp_vals = interpolate_fn(values[:-1], values[1:], pct)
     return indicator.dot(interp_vals) + (bounds[-1] <= count) * values[-1]
```