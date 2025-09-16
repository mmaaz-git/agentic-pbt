# Bug Report: optax.perturbations dtype Parameter Not Respected

**Target**: `optax.perturbations.Normal.sample` and `optax.perturbations.Gumbel.sample`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `sample()` methods of Normal and Gumbel distributions accept a `dtype` parameter but do not respect it when JAX's x64 mode is disabled (the default), returning float32 arrays even when float64 is explicitly requested.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import jax
import jax.numpy as jnp
import optax.perturbations as pert

@given(
    st.sampled_from([jnp.float32, jnp.float64]),
    st.sampled_from([pert.Normal(), pert.Gumbel()]),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=2**31-1)
)
def test_distribution_dtype_handling(dtype, distribution, size, seed):
    key = jax.random.key(seed)
    shape = (size,)
    
    samples = distribution.sample(key, shape, dtype=dtype)
    
    # Check dtype
    assert samples.dtype == dtype, f"Expected dtype {dtype}, got {samples.dtype}"
```

**Failing input**: `dtype=jnp.float64, distribution=Normal(), size=1, seed=0`

## Reproducing the Bug

```python
import jax
import jax.numpy as jnp
import optax.perturbations as pert

jax.config.update("jax_enable_x64", False)  # Default JAX configuration

normal = pert.Normal()
key = jax.random.key(0)

requested_dtype = jnp.float64
samples = normal.sample(key, sample_shape=(3,), dtype=requested_dtype)

print(f"Requested dtype: {requested_dtype}")  # <class 'jax.numpy.float64'>
print(f"Received dtype:  {samples.dtype}")    # float32

assert samples.dtype == requested_dtype  # AssertionError
```

## Why This Is A Bug

The `sample()` method signature explicitly accepts a `dtype` parameter, creating an API contract that the returned samples will have the requested dtype. When this parameter is silently ignored and a different dtype is returned, it violates the principle of least surprise and the documented API contract. This could lead to silent precision loss in user code that relies on specific dtypes.

## Fix

```diff
--- a/optax/perturbations/_make_pert.py
+++ b/optax/perturbations/_make_pert.py
@@ -34,7 +34,8 @@ class Normal:
       sample_shape: base.Shape = (),
       dtype: jax.typing.DTypeLike = float,
   ) -> jax.Array:
-    return jax.random.normal(key, sample_shape, dtype)
+    samples = jax.random.normal(key, sample_shape, dtype)
+    return samples.astype(dtype)  # Ensure output matches requested dtype
 
   def log_prob(self, inputs: jax.Array) -> jax.Array:
     return -0.5 * inputs**2
@@ -49,7 +50,8 @@ class Gumbel:
       sample_shape: base.Shape = (),
       dtype: jax.typing.DTypeLike = float,
   ) -> jax.Array:
-    return jax.random.gumbel(key, sample_shape, dtype)
+    samples = jax.random.gumbel(key, sample_shape, dtype)
+    return samples.astype(dtype)  # Ensure output matches requested dtype
 
   def log_prob(self, inputs: jax.Array) -> jax.Array:
     return -inputs - jnp.exp(-inputs)
```