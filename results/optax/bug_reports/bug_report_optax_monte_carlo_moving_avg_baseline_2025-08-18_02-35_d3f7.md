# Bug Report: optax.monte_carlo.moving_avg_baseline Division by Zero

**Target**: `optax.monte_carlo.moving_avg_baseline`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `moving_avg_baseline` function in optax.monte_carlo causes division by zero when `decay=1.0` and `zero_debias=True`, resulting in inf/nan values.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import jax.numpy as jnp
import optax.monte_carlo as mc

@given(
    initial_value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    sample_value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
def test_moving_avg_baseline_with_unit_decay_and_zero_debias(initial_value, sample_value):
    def simple_function(x):
        return float(x[0])
    
    # This configuration causes division by zero
    _, _, update_state = mc.moving_avg_baseline(
        simple_function, 
        decay=1.0,
        zero_debias=True,
        use_decay_early_training_heuristic=False
    )
    
    state = (jnp.array(initial_value), 0)
    samples = jnp.array([[sample_value]])
    new_state = update_state(None, samples, state)
    
    # The value should be finite, but it's not due to division by zero
    assert jnp.isfinite(new_state[0]), f"Division by zero: {new_state[0]}"
```

**Failing input**: Any input fails with `decay=1.0, zero_debias=True`

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax.monte_carlo as mc

def simple_function(x):
    return float(x[0])

_, _, update_state = mc.moving_avg_baseline(
    simple_function, 
    decay=1.0,
    zero_debias=True,
    use_decay_early_training_heuristic=False
)

state = (jnp.array(0.0), 0)
samples = jnp.array([[10.0]])

new_state = update_state(None, samples, state)
print(f"Result: {new_state[0]}")  # Output: inf or nan
assert jnp.isfinite(new_state[0])  # Fails
```

## Why This Is A Bug

When `decay=1.0` and `zero_debias=True`, the zero-debiasing denominator becomes `1 - decay^(i+1) = 1 - 1 = 0`, causing division by zero. This violates the expectation that the moving average baseline should always produce finite values for finite inputs. The function should either validate input parameters or handle this edge case gracefully.

## Fix

```diff
--- a/optax/monte_carlo/control_variates.py
+++ b/optax/monte_carlo/control_variates.py
@@ -206,7 +206,10 @@ def moving_avg_baseline(
     )
 
     if zero_debias:
-      updated_value /= jnp.ones([]) - jnp.power(iteration_decay, i + 1)
+      denominator = jnp.ones([]) - jnp.power(iteration_decay, i + 1)
+      # Avoid division by zero when decay=1.0
+      denominator = jnp.where(jnp.abs(denominator) < 1e-10, 1.0, denominator)
+      updated_value /= denominator
 
     return (jax.lax.stop_gradient(updated_value), i + 1)
```