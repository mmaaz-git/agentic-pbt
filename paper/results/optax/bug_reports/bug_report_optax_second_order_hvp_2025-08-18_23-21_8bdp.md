# Bug Report: optax.second_order.hvp Returns Dict Instead of Array for Nested Parameters

**Target**: `optax.second_order.hvp`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `hvp` function returns a nested dictionary structure when given nested parameters, violating its documented contract which states it returns "An Array".

## Property-Based Test

```python
def test_nested_params_hvp():
    """Test HVP with nested parameter structures."""
    params = {
        'weight': jnp.array([[1.0, 2.0]]),
        'bias': jnp.array([0.5])
    }
    
    inputs = jnp.array([[1.0, 0.5], [0.5, 1.0]])
    targets = jnp.array([1.5, 2.0])
    
    def loss_fn(params, inputs, targets):
        predictions = jnp.dot(inputs, params['weight'].T).squeeze() + params['bias']
        return jnp.mean((predictions - targets) ** 2)
    
    from jax import flatten_util
    flat_params, unflatten = flatten_util.ravel_pytree(params)
    param_size = flat_params.size
    
    v = jnp.ones(param_size)
    
    hvp_result = optax.second_order.hvp(loss_fn, v, params, inputs, targets)
    
    assert hvp_result.shape == (param_size,), f"HVP shape mismatch: {hvp_result.shape}"
```

**Failing input**: Nested parameter dictionary with `v = jnp.ones(3)`

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax.second_order
from jax import flatten_util

params = {
    'weight': jnp.array([[1.0, 2.0]]),
    'bias': jnp.array([0.5])
}

inputs = jnp.array([[1.0, 0.5], [0.5, 1.0]])
targets = jnp.array([1.5, 2.0])

def loss_fn(params, inputs, targets):
    predictions = jnp.dot(inputs, params['weight'].T).squeeze() + params['bias']
    return jnp.mean((predictions - targets) ** 2)

flat_params, _ = flatten_util.ravel_pytree(params)
v = jnp.ones(flat_params.size)

hvp_result = optax.second_order.hvp(loss_fn, v, params, inputs, targets)
print(type(hvp_result))  # <class 'dict'>
print(hvp_result)  # {'bias': Array([5.], dtype=float32), 'weight': Array([[3.75, 3.75]], dtype=float32)}
```

## Why This Is A Bug

The function's docstring clearly states it returns "An Array corresponding to the product of v and the Hessian", but it returns a nested dictionary when params is a nested structure. This violates the API contract and breaks code that expects a flattened array result.

## Fix

The function should flatten the result before returning it, similar to how the input vector `v` is expected to be flattened:

```diff
def hvp(
    loss: _base.LossFn,
    v: jax.Array,
    params: Any,
    inputs: jax.Array,
    targets: jax.Array,
) -> jax.Array:
  _, unravel_fn = flatten_util.ravel_pytree(params)
  loss_fn = lambda p: loss(p, inputs, targets)
-  return jax.jvp(jax.grad(loss_fn), [params], [unravel_fn(v)])[1]
+  result = jax.jvp(jax.grad(loss_fn), [params], [unravel_fn(v)])[1]
+  return flatten_util.ravel_pytree(result)[0]
```