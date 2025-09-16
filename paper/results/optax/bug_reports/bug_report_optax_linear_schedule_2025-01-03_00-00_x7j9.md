# Bug Report: optax.schedules.linear_schedule Precision Loss for Small Initial Values

**Target**: `optax.schedules.linear_schedule`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-01-03

## Summary

The `linear_schedule` function loses precision when `init_value` is very small compared to `end_value`, causing it to return an incorrect value at step 0 instead of the exact `init_value`.

## Property-Based Test

```python
@given(st.floats(min_value=-100, max_value=100, allow_nan=False),
       st.floats(min_value=-100, max_value=100, allow_nan=False),
       st.integers(min_value=1, max_value=1000))
@settings(max_examples=100) 
def test_linear_schedule_endpoints(init_val, end_val, transition_steps):
    """Test that linear_schedule has correct start and end values."""
    schedule_fn = optax.schedules.linear_schedule(
        init_value=init_val,
        end_value=end_val,
        transition_steps=transition_steps,
        transition_begin=0
    )
    
    # Check initial value
    start_val = schedule_fn(0)
    assert jnp.isclose(start_val, init_val, rtol=1e-5), \
        f"Linear schedule start value {start_val} != {init_val}"
```

**Failing input**: `init_val=3.474085623540969e-07, end_val=1.0, transition_steps=1`

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax

init_val = 3.474085623540969e-07
end_val = 1.0
transition_steps = 1

schedule_fn = optax.schedules.linear_schedule(
    init_value=init_val,
    end_value=end_val, 
    transition_steps=transition_steps,
    transition_begin=0
)

result = schedule_fn(0)
print(f"Expected: {init_val:.15e}")
print(f"Got:      {float(result):.15e}")
print(f"Equal:    {float(result) == init_val}")
```

## Why This Is A Bug

The schedule function should return exactly `init_value` at step 0 according to its mathematical definition. However, due to float32 precision loss in the formula `(init_value - end_value) * frac + end_value`, when `init_value` is very small relative to `end_value`, catastrophic cancellation occurs during the subtraction and re-addition of the large `end_value`.

## Fix

The issue is in the `polynomial_schedule` implementation that `linear_schedule` delegates to. The formula needs to be rewritten to avoid catastrophic cancellation:

```diff
--- a/optax/schedules/_schedule.py
+++ b/optax/schedules/_schedule.py
@@ -142,7 +142,12 @@ def polynomial_schedule(
   def schedule(count):
     count = jnp.clip(count - transition_begin, 0, transition_steps)
     frac = 1 - count / transition_steps
-    return (init_value - end_value) * (frac**power) + end_value
+    # Avoid catastrophic cancellation by special-casing edge values
+    if count == 0 and transition_begin == 0:
+      return init_value
+    elif count >= transition_steps:
+      return end_value
+    return init_value * (frac**power) + end_value * (1 - frac**power)
 
   return schedule
```

The alternative formula `init_value * (frac**power) + end_value * (1 - frac**power)` avoids the subtraction and re-addition pattern that causes precision loss.