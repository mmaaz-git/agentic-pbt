"""Test edge cases and special values in optax.tree module."""

import math
import jax.numpy as jnp
import numpy as np
import optax.tree
from hypothesis import assume, given, settings, strategies as st


def floats_with_special():
    """Float strategy including special values."""
    return st.one_of(
        st.just(0.0),
        st.just(-0.0),
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan')),
        st.floats(min_value=-1e10, max_value=1e10, width=32)
    )


@given(st.lists(floats_with_special(), min_size=1, max_size=5))
def test_zeros_with_special_values(values):
    """Test zeros_like with special float values."""
    tree = jnp.array(values, dtype=jnp.float32)
    zeros = optax.tree.zeros_like(tree)
    
    # Check shape is preserved
    assert zeros.shape == tree.shape, f"Shape not preserved: {zeros.shape} != {tree.shape}"
    
    # Check all values are zero (including when input has NaN/inf)
    assert jnp.all(zeros == 0.0), f"Not all zeros: {zeros}"


@given(st.lists(floats_with_special(), min_size=1, max_size=5))
def test_ones_with_special_values(values):
    """Test ones_like with special float values."""
    tree = jnp.array(values, dtype=jnp.float32)
    ones = optax.tree.ones_like(tree)
    
    # Check shape is preserved
    assert ones.shape == tree.shape, f"Shape not preserved"
    
    # Check all values are one
    assert jnp.all(ones == 1.0), f"Not all ones: {ones}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
             min_size=1, max_size=5),
    st.one_of(st.just(float('inf')), st.just(float('-inf')))
)
def test_scale_with_infinity(values, inf_scalar):
    """Test scale with infinite scalars."""
    tree = jnp.array(values, dtype=jnp.float32)
    result = optax.tree.scale(inf_scalar, tree)
    
    # Non-zero values scaled by inf should be inf (with appropriate sign)
    for i, val in enumerate(values):
        if val != 0:
            expected_sign = math.copysign(1, val * inf_scalar)
            assert math.isinf(result[i]), f"Expected inf at index {i}"
            assert math.copysign(1, result[i]) == expected_sign, f"Wrong sign at index {i}"
        else:
            # 0 * inf should be NaN
            assert math.isnan(result[i]), f"Expected NaN for 0*inf at index {i}, got {result[i]}"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
                min_size=1, max_size=5))
def test_scale_with_nan(values):
    """Test scale with NaN scalar."""
    tree = jnp.array(values, dtype=jnp.float32)
    result = optax.tree.scale(float('nan'), tree)
    
    # All results should be NaN
    assert jnp.all(jnp.isnan(result)), f"Not all NaN: {result}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
             min_size=1, max_size=5),
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
             min_size=1, max_size=5)
)
def test_vdot_conjugate_symmetry(values1, values2):
    """Test vdot(x, y) == conj(vdot(y, x)) for real values."""
    assume(len(values1) == len(values2))
    
    tree1 = jnp.array(values1, dtype=jnp.float32)
    tree2 = jnp.array(values2, dtype=jnp.float32)
    
    vdot_xy = optax.tree.vdot(tree1, tree2)
    vdot_yx = optax.tree.vdot(tree2, tree1)
    
    # For real values, vdot should be commutative
    assert jnp.allclose(vdot_xy, vdot_yx, rtol=1e-5), \
        f"vdot not commutative: {vdot_xy} != {vdot_yx}"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
                min_size=1, max_size=5))
def test_norm_zero_when_all_zeros(values):
    """Test norm of zero vector is zero."""
    zeros = jnp.zeros_like(jnp.array(values, dtype=jnp.float32))
    
    norm_val = optax.tree.norm(zeros)
    assert norm_val == 0.0, f"Norm of zero vector not zero: {norm_val}"
    
    norm_squared = optax.tree.norm(zeros, squared=True)
    assert norm_squared == 0.0, f"Squared norm of zero vector not zero: {norm_squared}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=0.1, max_value=1e6), 
             min_size=1, max_size=5),
    st.lists(st.just(0.0), min_size=1, max_size=5)
)
def test_div_by_zero(values, zeros):
    """Test division by zero behavior."""
    assume(len(values) == len(zeros))
    
    tree1 = jnp.array(values, dtype=jnp.float32)
    tree2 = jnp.array(zeros, dtype=jnp.float32)
    
    result = optax.tree.div(tree1, tree2)
    
    # Division by zero should give inf (for positive numerator)
    assert jnp.all(jnp.isinf(result)), f"Division by zero didn't give inf: {result}"
    assert jnp.all(result > 0), f"Wrong sign for division by zero: {result}"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
                min_size=2, max_size=10))
def test_sum_empty_like(values):
    """Test sum of zeros_like gives zero."""
    tree = jnp.array(values, dtype=jnp.float32)
    zeros = optax.tree.zeros_like(tree)
    
    sum_val = optax.tree.sum(zeros)
    assert sum_val == 0.0, f"Sum of zeros not zero: {sum_val}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
             min_size=2, max_size=5),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)
)
def test_add_associativity(values, a, b):
    """Test (tree + a) + b == tree + (a + b)"""
    tree = jnp.array(values, dtype=jnp.float32)
    tree_a = jnp.full_like(tree, a)
    tree_b = jnp.full_like(tree, b)
    
    # (tree + a) + b
    left = optax.tree.add(optax.tree.add(tree, tree_a), tree_b)
    
    # tree + (a + b)
    tree_ab = jnp.full_like(tree, a + b)
    right = optax.tree.add(tree, tree_ab)
    
    assert jnp.allclose(left, right, rtol=1e-5, atol=1e-6), \
        f"Add not associative: {left} != {right}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=1e-3, max_value=1e3), 
             min_size=2, max_size=5),
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=1e-3, max_value=1e3), 
             min_size=2, max_size=5)
)
def test_where_functionality(values1, values2):
    """Test where function with boolean conditions."""
    assume(len(values1) == len(values2))
    
    tree1 = jnp.array(values1, dtype=jnp.float32)
    tree2 = jnp.array(values2, dtype=jnp.float32)
    
    # Test with True - should return tree1
    result_true = optax.tree.where(True, tree1, tree2)
    assert jnp.array_equal(result_true, tree1), "where(True) didn't return tree1"
    
    # Test with False - should return tree2
    result_false = optax.tree.where(False, tree1, tree2)
    assert jnp.array_equal(result_false, tree2), "where(False) didn't return tree2"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])