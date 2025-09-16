# Bug Report: optax.exponential_decay Upper Bound Violation with Growth Rate

**Target**: `optax.exponential_decay`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

`exponential_decay` with `decay_rate > 1` (growth mode) violates its documented upper bound constraint due to floating-point precision issues in the clipping logic.

## Property-Based Test

```python
@given(
    init_value=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=100),
    decay_rate=st.floats(min_value=2.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=11.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
def test_exponential_decay_with_growth_and_upper_bound(init_value, transition_steps, decay_rate, end_value):
    schedule = optax.exponential_decay(
        init_value=init_value,
        transition_steps=transition_steps,
        decay_rate=decay_rate,
        transition_begin=0,
        staircase=False,
        end_value=end_value
    )
    
    for i in range(0, transition_steps * 2):
        result = float(schedule(i))
        assert result <= end_value + 1e-6, f"At step {i}: {result} > {end_value}"
```

**Failing input**: `init_value=2.0, transition_steps=3, decay_rate=9.0, end_value=64.68065431345092`

## Reproducing the Bug

```python
import optax

schedule = optax.exponential_decay(
    init_value=2.0,
    transition_steps=3,
    decay_rate=9.0,
    transition_begin=0,
    staircase=False,
    end_value=64.68065431345092
)

for step in [0, 5, 10]:
    result = float(schedule(step))
    print(f"Step {step}: {result}")
    if result > 64.68065431345092:
        print(f"  VIOLATION: exceeds upper bound by {result - 64.68065431345092}")
```

## Why This Is A Bug

According to the docstring, when `decay_rate > 1`, the `end_value` parameter should act as an upper bound. However, due to float32 precision limitations in JAX's computation, the clipped value slightly exceeds the specified upper bound. The violation is small (2.12e-06) but represents a contract violation where the function doesn't strictly enforce its documented constraint.

## Fix

The issue occurs because the computation and clipping happen in float32, leading to precision loss. A fix would ensure proper handling of the upper bound:

```diff
--- a/optax/schedules/_schedule.py
+++ b/optax/schedules/_schedule.py
@@ -320,7 +320,9 @@ def exponential_decay(
         decreased_count <= 0, init_value, init_value * jnp.power(decay_rate, p)
     )
     if end_value is not None:
-      decayed_value = clip_fn(decayed_value, end_value)
+      # Cast end_value to same dtype as decayed_value to ensure consistent precision
+      end_value_cast = jnp.asarray(end_value, dtype=decayed_value.dtype)
+      decayed_value = clip_fn(decayed_value, end_value_cast)
     return decayed_value
```