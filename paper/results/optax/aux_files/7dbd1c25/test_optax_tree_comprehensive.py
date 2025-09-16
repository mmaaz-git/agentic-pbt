"""Comprehensive property tests for optax.tree with complex structures."""

import jax.numpy as jnp
import optax.tree
from hypothesis import given, strategies as st, assume, settings
import numpy as np


@st.composite
def complex_pytree_strategy(draw):
    """Generate complex nested pytree structures."""
    # Generate a deeply nested structure
    base_array = draw(st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
        min_size=2, max_size=4
    ))
    
    structure = {
        'array': jnp.array(base_array, dtype=jnp.float32),
        'nested': {
            'a': jnp.array(draw(st.lists(
                st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
                min_size=2, max_size=4
            )), dtype=jnp.float32),
            'b': [
                jnp.array(draw(st.lists(
                    st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
                    min_size=2, max_size=4
                )), dtype=jnp.float32),
                jnp.array(draw(st.lists(
                    st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
                    min_size=2, max_size=4
                )), dtype=jnp.float32),
            ]
        },
        'tuple': (
            jnp.array(draw(st.lists(
                st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
                min_size=2, max_size=4
            )), dtype=jnp.float32),
        )
    }
    return structure


@st.composite
def matching_complex_pytrees(draw):
    """Generate two complex pytrees with matching structure."""
    template = draw(complex_pytree_strategy())
    
    def generate_matching(tmpl):
        if isinstance(tmpl, jnp.ndarray):
            return jnp.array(draw(st.lists(
                st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
                min_size=len(tmpl), max_size=len(tmpl)
            )), dtype=jnp.float32)
        elif isinstance(tmpl, dict):
            return {k: generate_matching(v) for k, v in tmpl.items()}
        elif isinstance(tmpl, list):
            return [generate_matching(item) for item in tmpl]
        elif isinstance(tmpl, tuple):
            return tuple(generate_matching(item) for item in tmpl)
        return tmpl
    
    tree2 = generate_matching(template)
    return template, tree2


@given(complex_pytree_strategy())
@settings(max_examples=50)
def test_complex_structure_preservation(tree):
    """Test that all operations preserve complex nested structures."""
    # Test zeros_like
    zeros = optax.tree.zeros_like(tree)
    assert_same_structure(tree, zeros)
    
    # Test ones_like
    ones = optax.tree.ones_like(tree)
    assert_same_structure(tree, ones)
    
    # Test scale
    scaled = optax.tree.scale(2.0, tree)
    assert_same_structure(tree, scaled)


@given(matching_complex_pytrees())
@settings(max_examples=50)
def test_complex_add_sub_inverse(trees):
    """Test add and sub are inverses with complex structures."""
    tree1, tree2 = trees
    
    # Forward and backward
    added = optax.tree.add(tree1, tree2)
    recovered = optax.tree.sub(added, tree2)
    
    assert trees_close(recovered, tree1, rtol=1e-4), \
        "Add-sub not inverse for complex structure"


@given(matching_complex_pytrees())
@settings(max_examples=50)
def test_complex_linear_combinations(trees):
    """Test linear combinations work correctly with complex structures."""
    tree1, tree2 = trees
    
    # Test: 2*tree1 + 3*tree2 == add(scale(2, tree1), scale(3, tree2))
    left = optax.tree.add(
        optax.tree.scale(2.0, tree1),
        optax.tree.scale(3.0, tree2)
    )
    
    # Compute expected manually
    def manual_linear_combo(t1, t2):
        if isinstance(t1, jnp.ndarray) and isinstance(t2, jnp.ndarray):
            return 2.0 * t1 + 3.0 * t2
        elif isinstance(t1, dict) and isinstance(t2, dict):
            return {k: manual_linear_combo(t1[k], t2[k]) for k in t1.keys()}
        elif isinstance(t1, list) and isinstance(t2, list):
            return [manual_linear_combo(x, y) for x, y in zip(t1, t2)]
        elif isinstance(t1, tuple) and isinstance(t2, tuple):
            return tuple(manual_linear_combo(x, y) for x, y in zip(t1, t2))
        return None
    
    expected = manual_linear_combo(tree1, tree2)
    
    assert trees_close(left, expected, rtol=1e-5), \
        "Linear combination failed for complex structure"


@given(complex_pytree_strategy())
@settings(max_examples=50)
def test_sum_norm_consistency(tree):
    """Test that sum and norm give consistent results."""
    # For a tree of all positive values, sum should be >= norm(tree, ord=1)
    # Make all values positive
    def make_positive(t):
        if isinstance(t, jnp.ndarray):
            return jnp.abs(t)
        elif isinstance(t, dict):
            return {k: make_positive(v) for k, v in t.items()}
        elif isinstance(t, list):
            return [make_positive(item) for item in t]
        elif isinstance(t, tuple):
            return tuple(make_positive(item) for item in t)
        return t
    
    pos_tree = make_positive(tree)
    
    tree_sum = optax.tree.sum(pos_tree)
    tree_norm_1 = optax.tree.norm(pos_tree, ord=1)
    
    # Sum of positive values equals L1 norm
    assert jnp.allclose(tree_sum, tree_norm_1, rtol=1e-5), \
        f"Sum != L1 norm for positive values: {tree_sum} != {tree_norm_1}"


@given(matching_complex_pytrees())
@settings(max_examples=50)
def test_mul_identity(trees):
    """Test multiplication by ones_like gives identity."""
    tree1, _ = trees
    
    ones = optax.tree.ones_like(tree1)
    result = optax.tree.mul(tree1, ones)
    
    assert trees_close(result, tree1, rtol=1e-5), \
        "Multiplication by ones didn't give identity"


@given(complex_pytree_strategy())
@settings(max_examples=50)
def test_where_with_complex_structure(tree):
    """Test where function preserves structure."""
    zeros = optax.tree.zeros_like(tree)
    
    # where(True, tree, zeros) should give tree
    result_true = optax.tree.where(True, tree, zeros)
    assert trees_close(result_true, tree), "where(True) failed"
    
    # where(False, tree, zeros) should give zeros
    result_false = optax.tree.where(False, tree, zeros)
    assert trees_close(result_false, zeros), "where(False) failed"


@given(
    complex_pytree_strategy(),
    st.floats(min_value=0.1, max_value=0.9)
)
@settings(max_examples=30)
def test_update_moment_with_complex_structure(tree, decay):
    """Test update_moment with complex nested structures."""
    # Initialize moments as zeros
    moments = optax.tree.zeros_like(tree)
    
    # First update
    moments = optax.tree.update_moment(tree, moments, decay, order=2)
    
    # Check structure is preserved
    assert_same_structure(tree, moments)
    
    # Check values are reasonable (should be (1-decay) * tree^2)
    expected_factor = 1 - decay
    
    def check_values(t, m):
        if isinstance(t, jnp.ndarray) and isinstance(m, jnp.ndarray):
            expected = expected_factor * (t ** 2)
            assert jnp.allclose(m, expected, rtol=1e-4), \
                f"Moment values incorrect: {m} != {expected}"
        elif isinstance(t, dict) and isinstance(m, dict):
            for k in t.keys():
                check_values(t[k], m[k])
        elif isinstance(t, (list, tuple)) and isinstance(m, (list, tuple)):
            for tv, mv in zip(t, m):
                check_values(tv, mv)
    
    check_values(tree, moments)


# Helper functions

def assert_same_structure(tree1, tree2):
    """Assert two pytrees have the same structure."""
    if isinstance(tree1, jnp.ndarray) and isinstance(tree2, jnp.ndarray):
        assert tree1.shape == tree2.shape, f"Shape mismatch: {tree1.shape} != {tree2.shape}"
    elif isinstance(tree1, dict) and isinstance(tree2, dict):
        assert set(tree1.keys()) == set(tree2.keys()), "Dict keys mismatch"
        for k in tree1.keys():
            assert_same_structure(tree1[k], tree2[k])
    elif isinstance(tree1, list) and isinstance(tree2, list):
        assert len(tree1) == len(tree2), f"List length mismatch: {len(tree1)} != {len(tree2)}"
        for t1, t2 in zip(tree1, tree2):
            assert_same_structure(t1, t2)
    elif isinstance(tree1, tuple) and isinstance(tree2, tuple):
        assert len(tree1) == len(tree2), f"Tuple length mismatch"
        for t1, t2 in zip(tree1, tree2):
            assert_same_structure(t1, t2)
    else:
        assert type(tree1) == type(tree2), f"Type mismatch: {type(tree1)} != {type(tree2)}"


def trees_close(tree1, tree2, rtol=1e-5, atol=1e-7):
    """Check if two pytrees are numerically close."""
    try:
        from jax.tree_util import tree_map, tree_flatten
        
        def allclose_fn(x, y):
            if isinstance(x, (jnp.ndarray, np.ndarray)) and isinstance(y, (jnp.ndarray, np.ndarray)):
                return jnp.allclose(x, y, rtol=rtol, atol=atol)
            return x == y
        
        results = tree_map(allclose_fn, tree1, tree2)
        flat_results, _ = tree_flatten(results)
        return all(flat_results)
    except:
        return False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])