# Bug Report: optax.contrib.normalize() Produces NaN with Zero Gradients

**Target**: `optax.contrib.normalize()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `normalize()` function in optax.contrib produces NaN values when applied to zero gradients, causing undefined behavior in gradient descent optimization.

## Property-Based Test

```python
from hypothesis import given, assume, strategies as st
import jax.numpy as jnp
import optax.contrib
import math

@given(gradient_trees())
def test_normalize_zero_gradient_stability(gradients):
    """Test normalize() handles zero gradients gracefully."""
    # Create zero gradients
    zero_grads = jax.tree.map(lambda x: jnp.zeros_like(x), gradients)
    
    # Initialize and apply normalize
    normalize_fn = optax.contrib.normalize()
    state = normalize_fn.init(zero_grads)
    normalized, _ = normalize_fn.update(zero_grads, state)
    
    # Should not produce NaN values
    for g in jax.tree.leaves(normalized):
        assert not jnp.any(jnp.isnan(g)), "normalize() produced NaN with zero gradients"
```

**Failing input**: Any tree structure with all zero values, e.g., `{'param': jnp.zeros(3)}`

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax.contrib

# Create zero gradients
zero_gradients = {'param': jnp.zeros(3)}

# Apply normalize transformation
normalize_fn = optax.contrib.normalize()
state = normalize_fn.init(zero_gradients)
normalized_grads, _ = normalize_fn.update(zero_gradients, state)

# Check for NaN
print(normalized_grads['param'])  # Output: [nan nan nan]
assert jnp.all(jnp.isnan(normalized_grads['param']))  # Confirms NaN values
```

## Why This Is A Bug

The normalize() function divides gradients by their global norm without checking for zero. When all gradients are zero, the global norm is zero, resulting in division by zero and NaN values. This violates expected numerical stability - optimization functions should handle edge cases gracefully. Zero gradients can occur in practice when:
- Training reaches a perfect minimum
- Certain layers are frozen
- Numerical underflow occurs

## Fix

```diff
--- a/optax/contrib/_sam.py
+++ b/optax/contrib/_sam.py
@@ -74,7 +74,10 @@ def normalize() -> base.GradientTransformation:
 
   def update_fn(updates, state, params=None):
     del params
     g_norm = utils.global_norm(updates)
-    updates = jax.tree.map(lambda g: g / g_norm, updates)
+    # Handle zero gradients gracefully
+    updates = jax.tree.map(
+        lambda g: jnp.where(g_norm > 1e-12, g / g_norm, g), 
+        updates)
     return updates, state
 
   return base.GradientTransformation(init_fn, update_fn)
```