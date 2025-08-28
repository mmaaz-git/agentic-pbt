"""Property-based tests for optax.tree module."""

import math
import jax.numpy as jnp
import numpy as np
import optax.tree
from hypothesis import assume, given, settings, strategies as st


def floats_strategy(allow_nan=False, allow_infinity=False):
    """Safe float strategy for numerical operations."""
    return st.floats(
        allow_nan=allow_nan,
        allow_infinity=allow_infinity,
        min_value=-1e6,
        max_value=1e6,
        width=32
    )


def array_strategy(min_size=1, max_size=10):
    """Generate JAX arrays."""
    return st.lists(
        floats_strategy(),
        min_size=min_size,
        max_size=max_size
    ).map(lambda x: jnp.array(x, dtype=jnp.float32))


@st.composite
def pytree_strategy(draw, max_depth=3, current_depth=0):
    """Generate nested pytree structures."""
    if current_depth >= max_depth:
        return draw(array_strategy())
    
    # Choose structure type
    structure_type = draw(st.sampled_from(['array', 'dict', 'list', 'tuple']))
    
    if structure_type == 'array':
        return draw(array_strategy())
    elif structure_type == 'dict':
        n_keys = draw(st.integers(min_value=1, max_value=3))
        keys = [f'key_{i}' for i in range(n_keys)]
        values = [draw(pytree_strategy(max_depth, current_depth + 1)) for _ in range(n_keys)]
        return dict(zip(keys, values))
    elif structure_type == 'list':
        n_elements = draw(st.integers(min_value=1, max_value=3))
        return [draw(pytree_strategy(max_depth, current_depth + 1)) for _ in range(n_elements)]
    else:  # tuple
        n_elements = draw(st.integers(min_value=1, max_value=3))
        return tuple(draw(pytree_strategy(max_depth, current_depth + 1)) for _ in range(n_elements))


@st.composite
def matching_pytrees_strategy(draw):
    """Generate two pytrees with the same structure."""
    structure = draw(pytree_strategy(max_depth=2))
    
    def generate_same_structure(template):
        if isinstance(template, jnp.ndarray):
            return draw(array_strategy(min_size=len(template), max_size=len(template)))
        elif isinstance(template, dict):
            return {k: generate_same_structure(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [generate_same_structure(item) for item in template]
        elif isinstance(template, tuple):
            return tuple(generate_same_structure(item) for item in template)
        else:
            return template
    
    tree1 = structure
    tree2 = generate_same_structure(structure)
    return tree1, tree2


def trees_allclose(tree1, tree2, rtol=1e-5, atol=1e-7):
    """Check if two pytrees are close within tolerance."""
    def allclose_fn(x, y):
        if isinstance(x, (jnp.ndarray, np.ndarray)) and isinstance(y, (jnp.ndarray, np.ndarray)):
            return jnp.allclose(x, y, rtol=rtol, atol=atol)
        return x == y
    
    try:
        from jax.tree_util import tree_map
        results = tree_map(allclose_fn, tree1, tree2)
        from jax.tree_util import tree_flatten
        flat_results, _ = tree_flatten(results)
        return all(flat_results)
    except:
        return False


@given(pytree_strategy())
@settings(max_examples=100)
def test_additive_identity(tree):
    """Test: add(tree, zeros_like(tree)) == tree"""
    zeros = optax.tree.zeros_like(tree)
    result = optax.tree.add(tree, zeros)
    assert trees_allclose(result, tree), f"Additive identity failed"


@given(pytree_strategy())
@settings(max_examples=100)
def test_multiplicative_identity(tree):
    """Test: scale(1.0, tree) == tree"""
    result = optax.tree.scale(1.0, tree)
    assert trees_allclose(result, tree), f"Multiplicative identity failed"


@given(
    pytree_strategy(),
    floats_strategy(),
    floats_strategy()
)
@settings(max_examples=100)
def test_scale_distributivity(tree, a, b):
    """Test: scale(a+b, tree) == add(scale(a, tree), scale(b, tree))"""
    assume(not math.isnan(a + b))
    assume(abs(a) < 1e3 and abs(b) < 1e3)
    
    left = optax.tree.scale(a + b, tree)
    right = optax.tree.add(
        optax.tree.scale(a, tree),
        optax.tree.scale(b, tree)
    )
    assert trees_allclose(left, right, rtol=1e-4, atol=1e-6), f"Distributivity failed for a={a}, b={b}"


@given(matching_pytrees_strategy())
@settings(max_examples=100)
def test_add_commutativity(trees):
    """Test: add(tree1, tree2) == add(tree2, tree1)"""
    tree1, tree2 = trees
    result1 = optax.tree.add(tree1, tree2)
    result2 = optax.tree.add(tree2, tree1)
    assert trees_allclose(result1, result2), f"Add commutativity failed"


@given(matching_pytrees_strategy())
@settings(max_examples=100)
def test_add_sub_round_trip(trees):
    """Test: sub(add(tree1, tree2), tree2) == tree1"""
    tree1, tree2 = trees
    added = optax.tree.add(tree1, tree2)
    result = optax.tree.sub(added, tree2)
    assert trees_allclose(result, tree1, rtol=1e-4, atol=1e-6), f"Add-sub round trip failed"


@given(matching_pytrees_strategy())
@settings(max_examples=100)
def test_sum_linearity(trees):
    """Test: sum(add(tree1, tree2)) == sum(tree1) + sum(tree2)"""
    tree1, tree2 = trees
    
    sum_of_add = optax.tree.sum(optax.tree.add(tree1, tree2))
    sum_separate = optax.tree.sum(tree1) + optax.tree.sum(tree2)
    
    assert jnp.allclose(sum_of_add, sum_separate, rtol=1e-5, atol=1e-7), \
        f"Sum linearity failed: {sum_of_add} != {sum_separate}"


@given(pytree_strategy())
@settings(max_examples=100)
def test_vdot_norm_relationship(tree):
    """Test: vdot(tree, tree) == norm(tree, squared=True)"""
    vdot_result = optax.tree.vdot(tree, tree)
    norm_squared = optax.tree.norm(tree, squared=True)
    
    assert jnp.allclose(vdot_result, norm_squared, rtol=1e-5, atol=1e-7), \
        f"Vdot-norm relationship failed: vdot={vdot_result}, norm^2={norm_squared}"


@given(pytree_strategy())
@settings(max_examples=100)
def test_norm_non_negative(tree):
    """Test: norm(tree) >= 0"""
    norm_val = optax.tree.norm(tree)
    assert norm_val >= 0, f"Norm is negative: {norm_val}"


@given(
    pytree_strategy(),
    floats_strategy()
)
@settings(max_examples=100)
def test_scale_vdot_relationship(tree, scalar):
    """Test: vdot(scale(a, tree), tree) == a * vdot(tree, tree)"""
    assume(abs(scalar) < 1e3)
    
    scaled = optax.tree.scale(scalar, tree)
    vdot_scaled = optax.tree.vdot(scaled, tree)
    vdot_original = optax.tree.vdot(tree, tree)
    expected = scalar * vdot_original
    
    assert jnp.allclose(vdot_scaled, expected, rtol=1e-4, atol=1e-6), \
        f"Scale-vdot relationship failed: {vdot_scaled} != {expected}"


@given(matching_pytrees_strategy())
@settings(max_examples=100)
def test_zeros_ones_structure(trees):
    """Test that zeros_like and ones_like preserve structure."""
    tree1, _ = trees
    
    zeros = optax.tree.zeros_like(tree1)
    ones = optax.tree.ones_like(tree1)
    
    # Check structure preservation
    def check_structure(template, generated, expected_val):
        if isinstance(template, jnp.ndarray) and isinstance(generated, jnp.ndarray):
            assert template.shape == generated.shape, f"Shape mismatch"
            assert jnp.allclose(generated, expected_val), f"Values not all {expected_val}"
        elif isinstance(template, dict) and isinstance(generated, dict):
            assert set(template.keys()) == set(generated.keys()), "Dict keys mismatch"
            for k in template.keys():
                check_structure(template[k], generated[k], expected_val)
        elif isinstance(template, (list, tuple)):
            assert len(template) == len(generated), "Length mismatch"
            assert type(template) == type(generated), "Type mismatch"
            for t, g in zip(template, generated):
                check_structure(t, g, expected_val)
    
    check_structure(tree1, zeros, 0.0)
    check_structure(tree1, ones, 1.0)


@given(matching_pytrees_strategy())
@settings(max_examples=100)
def test_mul_div_round_trip(trees):
    """Test: div(mul(tree1, tree2), tree2) ≈ tree1 (when tree2 has no zeros)"""
    tree1, tree2 = trees
    
    # Ensure tree2 has no zeros
    def add_small_value(x):
        if isinstance(x, jnp.ndarray):
            return jnp.where(jnp.abs(x) < 1e-6, 1e-3, x)
        return x
    
    from jax.tree_util import tree_map
    tree2_no_zeros = tree_map(add_small_value, tree2)
    
    multiplied = optax.tree.mul(tree1, tree2_no_zeros)
    result = optax.tree.div(multiplied, tree2_no_zeros)
    
    assert trees_allclose(result, tree1, rtol=1e-3, atol=1e-5), \
        f"Mul-div round trip failed"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])