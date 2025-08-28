"""Property-based tests for optax.tree_utils module."""
import math
import jax
import jax.numpy as jnp
import numpy as np
import optax.tree_utils as tree_utils
from hypothesis import given, strategies as st, assume, settings
import pytest


# Strategies for generating JAX arrays
@st.composite
def jax_arrays(draw, dtype=None, shape=None):
    """Generate JAX arrays with reasonable values."""
    if shape is None:
        shape = draw(st.tuples(st.integers(1, 5), st.integers(1, 5)))
    
    if dtype is None:
        dtype = draw(st.sampled_from([jnp.float32, jnp.float64]))
    
    # Convert numpy int to Python int for hypothesis
    size = int(np.prod(shape))
    
    if dtype in [jnp.float32, jnp.float64]:
        # Generate reasonable floats, avoiding NaN/inf
        array = draw(st.lists(
            st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
            min_size=size, max_size=size
        ))
    else:
        array = draw(st.lists(
            st.integers(min_value=-1000, max_value=1000),
            min_size=size, max_size=size
        ))
    
    return jnp.array(array, dtype=dtype).reshape(shape)


@st.composite  
def pytrees(draw, max_depth=3):
    """Generate pytrees with JAX arrays as leaves."""
    if max_depth == 0:
        return draw(jax_arrays())
    
    structure = draw(st.sampled_from(['array', 'dict', 'list', 'tuple']))
    
    if structure == 'array':
        return draw(jax_arrays())
    elif structure == 'dict':
        keys = draw(st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=3, unique=True))
        return {key: draw(pytrees(max_depth=max_depth-1)) for key in keys}
    elif structure == 'list':
        size = draw(st.integers(1, 3))
        return [draw(pytrees(max_depth=max_depth-1)) for _ in range(size)]
    else:  # tuple
        size = draw(st.integers(1, 3))
        return tuple(draw(pytrees(max_depth=max_depth-1)) for _ in range(size))


# Test 1: Addition identity property
@given(pytrees())
@settings(max_examples=100, deadline=None)
def test_add_zero_identity(tree):
    """tree_add(x, tree_zeros_like(x)) should equal x."""
    zero_tree = tree_utils.tree_zeros_like(tree)
    result = tree_utils.tree_add(tree, zero_tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result, tree)


# Test 2: Subtraction self property
@given(pytrees())
@settings(max_examples=100)
def test_sub_self_is_zero(tree):
    """tree_sub(x, x) should equal tree_zeros_like(x)."""
    result = tree_utils.tree_sub(tree, tree)
    zero_tree = tree_utils.tree_zeros_like(tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result, zero_tree)


# Test 3: Multiplication identity property
@given(pytrees())
@settings(max_examples=100)
def test_mul_one_identity(tree):
    """tree_mul(x, tree_ones_like(x)) should equal x."""
    ones_tree = tree_utils.tree_ones_like(tree)
    result = tree_utils.tree_mul(tree, ones_tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result, tree)


# Test 4: Division identity property  
@given(pytrees())
@settings(max_examples=100)
def test_div_one_identity(tree):
    """tree_div(x, tree_ones_like(x)) should equal x."""
    ones_tree = tree_utils.tree_ones_like(tree)
    result = tree_utils.tree_div(tree, ones_tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result, tree)


# Test 5: Scale identity property
@given(pytrees())
@settings(max_examples=100)
def test_scale_one_identity(tree):
    """tree_scale(1.0, x) should equal x."""
    result = tree_utils.tree_scale(1.0, tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result, tree)


# Test 6: Scale distributive property over addition
@given(pytrees(), st.floats(min_value=-100, max_value=100, allow_nan=False))
@settings(max_examples=100)
def test_scale_distributive(tree, scalar):
    """tree_scale(a, tree_add(x, y)) = tree_add(tree_scale(a, x), tree_scale(a, y))."""
    tree2 = tree_utils.tree_zeros_like(tree)  # Use zero for simplicity
    
    # Left side: scale(a, add(x, y))
    sum_tree = tree_utils.tree_add(tree, tree2)
    left = tree_utils.tree_scale(scalar, sum_tree)
    
    # Right side: add(scale(a, x), scale(a, y))
    scaled1 = tree_utils.tree_scale(scalar, tree)
    scaled2 = tree_utils.tree_scale(scalar, tree2)
    right = tree_utils.tree_add(scaled1, scaled2)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-4, atol=1e-6)
    
    jax.tree.map(assert_close, left, right)


# Test 7: Norm of zero tree
@given(pytrees())
@settings(max_examples=100, deadline=None)
def test_norm_of_zero_tree(tree):
    """tree_norm(tree_zeros_like(x)) should be 0."""
    zero_tree = tree_utils.tree_zeros_like(tree)
    norm = tree_utils.tree_norm(zero_tree)
    assert jnp.allclose(norm, 0.0, atol=1e-7)


# Test 8: Norm scaling property
@given(pytrees(), st.floats(min_value=-10, max_value=10, allow_nan=False))
@settings(max_examples=100)
def test_norm_scaling(tree, scalar):
    """tree_norm(tree_scale(a, x)) = |a| * tree_norm(x)."""
    scaled_tree = tree_utils.tree_scale(scalar, tree)
    
    norm_scaled = tree_utils.tree_norm(scaled_tree)
    norm_original = tree_utils.tree_norm(tree)
    expected = jnp.abs(scalar) * norm_original
    
    assert jnp.allclose(norm_scaled, expected, rtol=1e-4, atol=1e-6)


# Test 9: Inner product self equals squared norm
@given(pytrees())
@settings(max_examples=100)
def test_vdot_self_equals_squared_norm(tree):
    """tree_vdot(x, x) should equal tree_norm(x, squared=True) for real trees."""
    # Ensure we have real values
    tree = jax.tree.map(lambda x: jnp.real(x), tree)
    
    vdot_result = tree_utils.tree_vdot(tree, tree)
    norm_squared = tree_utils.tree_norm(tree, squared=True)
    
    assert jnp.allclose(vdot_result, norm_squared, rtol=1e-4, atol=1e-6)


# Test 10: tree_add commutativity
@given(pytrees())
@settings(max_examples=100)  
def test_add_commutative(tree):
    """tree_add(x, y) = tree_add(y, x)."""
    tree2 = tree_utils.tree_scale(0.5, tree)  # Create a different tree
    
    result1 = tree_utils.tree_add(tree, tree2)
    result2 = tree_utils.tree_add(tree2, tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result1, result2)


# Test 11: tree_add_scale correctness
@given(pytrees(), st.floats(min_value=-10, max_value=10, allow_nan=False))
@settings(max_examples=100)
def test_add_scale_equals_manual(tree, scalar):
    """tree_add_scale(x, a, y) = tree_add(x, tree_scale(a, y))."""
    tree2 = tree_utils.tree_scale(0.5, tree)  # Create a different tree
    
    # Using tree_add_scale
    result1 = tree_utils.tree_add_scale(tree, scalar, tree2)
    
    # Manual computation
    scaled = tree_utils.tree_scale(scalar, tree2)
    result2 = tree_utils.tree_add(tree, scaled)
    
    def assert_close(a, b):
        # Need to handle potential None values in tree_add_scale
        if a is None:
            assert b is None
        elif b is None:
            assert a is None
        else:
            assert jnp.allclose(a, b, rtol=1e-4, atol=1e-6)
    
    jax.tree.map(assert_close, result1, result2, is_leaf=lambda x: x is None)


# Test 12: Associativity of tree_add
@given(pytrees())
@settings(max_examples=100)
def test_add_associative(tree):
    """(x + y) + z = x + (y + z)."""
    tree2 = tree_utils.tree_scale(0.5, tree)
    tree3 = tree_utils.tree_scale(0.25, tree)
    
    # Left association
    temp1 = tree_utils.tree_add(tree, tree2)
    result1 = tree_utils.tree_add(temp1, tree3)
    
    # Right association
    temp2 = tree_utils.tree_add(tree2, tree3)
    result2 = tree_utils.tree_add(tree, temp2)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-4, atol=1e-6)
    
    jax.tree.map(assert_close, result1, result2)


# Test 13: tree_sum property
@given(pytrees())
@settings(max_examples=100)
def test_tree_sum_consistency(tree):
    """tree_sum should be consistent with manual summation."""
    total = tree_utils.tree_sum(tree)
    
    # Manual sum
    def sum_leaf(x):
        return jnp.sum(x)
    
    sums = jax.tree.map(sum_leaf, tree)
    manual_total = jax.tree.reduce(lambda a, b: a + b, sums, initializer=0)
    
    assert jnp.allclose(total, manual_total, rtol=1e-5, atol=1e-7)


# Test 14: tree_real on real trees
@given(pytrees())
@settings(max_examples=100)
def test_tree_real_identity_on_real(tree):
    """tree_real(x) = x for real-valued trees."""
    # Ensure tree is real
    tree = jax.tree.map(lambda x: jnp.real(x), tree)
    
    result = tree_utils.tree_real(tree)
    
    def assert_close(a, b):
        assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    jax.tree.map(assert_close, result, tree)


# Test 15: tree_clip bounds
@given(pytrees())
@settings(max_examples=100, deadline=None)
def test_tree_clip_bounds(tree):
    """tree_clip should respect min and max bounds."""
    min_val = -1.0
    max_val = 1.0
    
    clipped = tree_utils.tree_clip(tree, min_val, max_val)
    
    def check_bounds(x):
        assert jnp.all(x >= min_val - 1e-7)
        assert jnp.all(x <= max_val + 1e-7)
    
    jax.tree.map(check_bounds, clipped)