# Bug Report: optax.second_order.hvp Crashes with Scalar Parameters

**Target**: `optax.second_order.hvp`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `hvp` function crashes with a ValueError when given scalar parameters, failing to handle this valid use case.

## Property-Based Test

```python
def test_single_parameter():
    """Test with a single scalar parameter."""
    params = jnp.array(2.0)  # Single scalar parameter
    inputs = jnp.array([[1.0], [2.0], [3.0]])
    targets = jnp.array([2.0, 4.0, 6.0])
    
    def loss_fn(p, x, t):
        pred = x.squeeze() * p
        return jnp.mean((pred - t) ** 2)
    
    hvp_result = optax.second_order.hvp(loss_fn, jnp.array(1.0), params, inputs, targets)
    
    assert hvp_result.size == 1, f"HVP size should be 1, got {hvp_result.size}"
```

**Failing input**: `params = jnp.array(2.0)`, `v = jnp.array(1.0)`

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax.second_order

params = jnp.array(2.0)
inputs = jnp.array([[1.0], [2.0], [3.0]])
targets = jnp.array([2.0, 4.0, 6.0])

def loss_fn(p, x, t):
    pred = x.squeeze() * p
    return jnp.mean((pred - t) ** 2)

v = jnp.array(1.0)

hvp_result = optax.second_order.hvp(loss_fn, v, params, inputs, targets)
```

## Why This Is A Bug

Scalar parameters are a valid use case in optimization (e.g., learning rates, single weights). The function should handle scalar parameters gracefully, but instead crashes with "ValueError: axis 0 is out of bounds for array of dimension 0" in the internal flattening logic.

## Fix

The issue occurs in JAX's internal `_unravel_list_single_dtype` function when trying to split a scalar array. The fix requires handling the scalar case specially in the unraveling logic, or ensuring scalars are properly handled in the flatten_util operations. A workaround could be to reshape scalars to 1D arrays internally:

```diff
def hvp(
    loss: _base.LossFn,
    v: jax.Array,
    params: Any,
    inputs: jax.Array,
    targets: jax.Array,
) -> jax.Array:
+  # Handle scalar parameters
+  v = jnp.atleast_1d(v)
   _, unravel_fn = flatten_util.ravel_pytree(params)
   loss_fn = lambda p: loss(p, inputs, targets)
-  return jax.jvp(jax.grad(loss_fn), [params], [unravel_fn(v)])[1]
+  result = jax.jvp(jax.grad(loss_fn), [params], [unravel_fn(v)])[1]
+  # Ensure result is properly shaped
+  return flatten_util.ravel_pytree(result)[0]
```