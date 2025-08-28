# Bug Report: optax.projections.projection_simplex Violates Idempotence

**Target**: `optax.projections.projection_simplex`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The simplex projection function violates the mathematical property of idempotence - projecting a point twice produces a different result than projecting once, with small numerical differences appearing in the bias term.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import jax.numpy as jnp
import optax.projections as proj

@given(
    tree={'weights': st.lists(st.floats(min_value=-1000, max_value=1000,
                                        allow_nan=False, allow_infinity=False),
                             min_size=1, max_size=30).map(lambda lst: jnp.array(lst)),
          'bias': st.floats(min_value=-100, max_value=100, allow_nan=False)},
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100)
def test_simplex_idempotence(tree, scale):
    once = proj.projection_simplex(tree, scale)
    twice = proj.projection_simplex(once, scale)
    
    # Check weights are unchanged
    assert jnp.allclose(once['weights'], twice['weights'], rtol=1e-5, atol=1e-7)
    # Check bias is unchanged
    assert jnp.allclose(once['bias'], twice['bias'], rtol=1e-5, atol=1e-7)
```

**Failing input**: Tree with 30 mixed positive/negative values and near-zero bias, scale=49.53

## Reproducing the Bug

```python
import jax.numpy as jnp
import optax.projections as proj
import optax.tree as tree_utils

tree = {
    'weights': jnp.array([
        -172.349, -936.565, 184.947, 1.396e-88, 0.0, -0.99999,
        -608.465, 290.727, -272.863, 447.099, 970.114, -5.716e-251,
        -4.762e-158, 691.989, 2.183e-269, 110.925, 999.0, 442.260,
        -6.104e-05, -2.565e-157, -6.387e-83, -509.034, -309.718,
        585.316, 593.708, -7.286e-212, 1.216e-186, 0.5, -645.844, -3.032e-72
    ]),
    'bias': 1.113e-308
}
scale = 49.533

once = proj.projection_simplex(tree, scale)
twice = proj.projection_simplex(once, scale)

print(f"Bias after first projection: {once['bias']}")
print(f"Bias after second projection: {twice['bias']}")
print(f"Difference: {twice['bias'] - once['bias']}")
print(f"Are they equal? {jnp.allclose(once['bias'], twice['bias'], atol=1e-7)}")
```

## Why This Is A Bug

Mathematical projections onto convex sets should be idempotent: P(P(x)) = P(x). This is a fundamental property that ensures consistency. The simplex projection fails this property due to numerical precision issues when dealing with trees containing very small or zero bias values. While the weights remain stable, the bias term changes by small amounts (around 3e-6) on the second projection.

## Fix

The issue appears to be related to numerical precision in handling near-zero values in tree structures. The fix would involve:

1. Ensuring consistent handling of very small values (< machine epsilon) in the tree flattening/unraveling process
2. Adding explicit checks for values that should remain zero after projection
3. Improving the numerical stability of the internal `_projection_unit_simplex` function when dealing with mixed-scale inputs