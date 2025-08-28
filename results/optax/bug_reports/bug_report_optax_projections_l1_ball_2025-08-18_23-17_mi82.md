# Bug Report: optax.projections.projection_l1_ball Violates Constraint and Idempotence

**Target**: `optax.projections.projection_l1_ball`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The L1 ball projection function violates its mathematical constraint by producing outputs with L1 norm exceeding the specified scale, and fails to be idempotent (projecting twice gives different results than projecting once).

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import jax.numpy as jnp
import optax.projections as proj
import optax.tree as tree_utils

@given(
    tree={'weights': st.lists(st.floats(min_value=-1000, max_value=1000, 
                                        allow_nan=False, allow_infinity=False),
                             min_size=1, max_size=100).map(lambda lst: jnp.array(lst)),
          'bias': st.floats(min_value=-100, max_value=100, allow_nan=False)},
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100)
def test_l1_ball_constraint_and_idempotence(tree, scale):
    # Test constraint satisfaction
    result = proj.projection_l1_ball(tree, scale)
    norm = tree_utils.norm(result, ord=1)
    assert norm <= scale * (1 + 1e-5), f"Norm {norm} exceeds scale {scale}"
    
    # Test idempotence
    twice = proj.projection_l1_ball(result, scale)
    assert jnp.allclose(result['weights'], twice['weights'], rtol=1e-5, atol=1e-7)
    assert jnp.allclose(result['bias'], twice['bias'], rtol=1e-5, atol=1e-7)
```

**Failing input**: `tree={'weights': jnp.array([344.649]), 'bias': 0.0}, scale=0.1`

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax.projections as proj
import optax.tree as tree_utils

tree = {'weights': jnp.array([344.649]), 'bias': 0.0}
scale = 0.1

# First projection
result = proj.projection_l1_ball(tree, scale)
print(f"L1 norm after projection: {tree_utils.norm(result, ord=1)}")
print(f"Expected maximum: {scale}")

# Second projection (idempotence test)
result2 = proj.projection_l1_ball(result, scale)
print(f"First projection weights: {result['weights']}")
print(f"Second projection weights: {result2['weights']}")
print(f"Are they equal? {jnp.allclose(result['weights'], result2['weights'])}")
```

## Why This Is A Bug

The projection_l1_ball function is documented to solve the constrained optimization problem where ||y||_1 <= scale. However, it produces outputs that violate this constraint. Additionally, mathematical projections should be idempotent (P(P(x)) = P(x)), but this implementation fails this fundamental property. The first projection produces a norm of 0.1000061 (exceeding the constraint), and projecting again changes the result to exactly 0.1.

## Fix

The bug appears to be in the internal projection algorithm's numerical precision. The implementation should ensure strict constraint satisfaction. Without access to the internal implementation, a high-level fix would involve:

1. Adding a final clipping step to ensure the L1 norm never exceeds the scale
2. Improving the numerical stability of the projection algorithm
3. Adding tolerance checks in the core projection routine to handle edge cases with large input values