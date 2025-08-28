"""Final property tests for remaining optax.tree functions."""

import jax.numpy as jnp
import optax.tree
from hypothesis import given, strategies as st, assume, settings
import numpy as np


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
             min_size=2, max_size=5),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-50, max_value=50),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-50, max_value=50)
)
def test_clip_properties(values, min_val, max_val):
    """Test clip function properties."""
    assume(min_val <= max_val)
    
    tree = jnp.array(values, dtype=jnp.float32)
    
    # Test clipping
    clipped = optax.tree.clip(tree, min_val, max_val)
    
    # All values should be within bounds
    assert jnp.all(clipped >= min_val - 1e-6), f"Values below min: {clipped[clipped < min_val]}"
    assert jnp.all(clipped <= max_val + 1e-6), f"Values above max: {clipped[clipped > max_val]}"
    
    # Values already in range should be unchanged
    mask = (tree >= min_val) & (tree <= max_val)
    if jnp.any(mask):
        assert jnp.allclose(clipped[mask], tree[mask]), "In-range values modified"
    
    # Test with None bounds
    clipped_no_min = optax.tree.clip(tree, None, max_val)
    assert jnp.all(clipped_no_min <= max_val + 1e-6), "Clip with None min failed"
    
    clipped_no_max = optax.tree.clip(tree, min_val, None)
    assert jnp.all(clipped_no_max >= min_val - 1e-6), "Clip with None max failed"
    
    clipped_no_bounds = optax.tree.clip(tree, None, None)
    assert jnp.array_equal(clipped_no_bounds, tree), "Clip with no bounds should be identity"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
                min_size=2, max_size=5))
def test_clip_idempotence(values):
    """Test that clipping twice gives the same result."""
    tree = jnp.array(values, dtype=jnp.float32)
    
    # Clip once
    clipped_once = optax.tree.clip(tree, -10.0, 10.0)
    
    # Clip again with same bounds
    clipped_twice = optax.tree.clip(clipped_once, -10.0, 10.0)
    
    assert jnp.array_equal(clipped_once, clipped_twice), "Clipping not idempotent"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
                min_size=2, max_size=5))
def test_cast_preserves_values(values):
    """Test that casting preserves values within precision limits."""
    tree = jnp.array(values, dtype=jnp.float32)
    
    # Cast to float64 and back
    tree_f64 = optax.tree.cast(tree, jnp.float64)
    tree_back = optax.tree.cast(tree_f64, jnp.float32)
    
    assert jnp.allclose(tree_back, tree, rtol=1e-6), "Cast round-trip failed"
    
    # Cast to same dtype should be identity
    tree_same = optax.tree.cast(tree, jnp.float32)
    assert jnp.array_equal(tree_same, tree), "Cast to same dtype not identity"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
                min_size=2, max_size=5),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10))
def test_full_like_properties(values, fill_value):
    """Test full_like creates arrays with correct fill value."""
    tree = jnp.array(values, dtype=jnp.float32)
    
    filled = optax.tree.full_like(tree, fill_value)
    
    # Check shape preserved
    assert filled.shape == tree.shape, "Shape not preserved"
    
    # Check all values are fill_value
    assert jnp.allclose(filled, fill_value), f"Not all values are {fill_value}: {filled}"
    
    # full_like with 0 should equal zeros_like
    filled_zero = optax.tree.full_like(tree, 0.0)
    zeros = optax.tree.zeros_like(tree)
    assert jnp.array_equal(filled_zero, zeros), "full_like(0) != zeros_like"
    
    # full_like with 1 should equal ones_like
    filled_one = optax.tree.full_like(tree, 1.0)
    ones = optax.tree.ones_like(tree)
    assert jnp.array_equal(filled_one, ones), "full_like(1) != ones_like"


@given(st.lists(st.complex_numbers(allow_nan=False, allow_infinity=False), min_size=2, max_size=5))
def test_conj_properties(complex_values):
    """Test conjugate properties with complex numbers."""
    tree = jnp.array(complex_values, dtype=jnp.complex64)
    
    # Test conjugate
    conj_tree = optax.tree.conj(tree)
    
    # Conjugate twice should give original
    conj_conj = optax.tree.conj(conj_tree)
    assert jnp.allclose(conj_conj, tree), "conj(conj(x)) != x"
    
    # For real numbers, conjugate should be identity
    real_tree = jnp.array([v.real for v in complex_values], dtype=jnp.float32)
    conj_real = optax.tree.conj(real_tree)
    assert jnp.array_equal(conj_real, real_tree), "conj of real != identity"


@given(st.lists(st.complex_numbers(allow_nan=False, allow_infinity=False), min_size=2, max_size=5))
def test_real_properties(complex_values):
    """Test real part extraction."""
    tree = jnp.array(complex_values, dtype=jnp.complex64)
    
    real_part = optax.tree.real(tree)
    
    # Real part should be real-valued
    assert jnp.isrealobj(real_part), "Real part not real"
    
    # For real input, should be identity
    real_tree = jnp.array([v.real for v in complex_values], dtype=jnp.float32)
    real_of_real = optax.tree.real(real_tree)
    assert jnp.array_equal(real_of_real, real_tree), "real of real != identity"


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
                 min_size=2, max_size=3),
        min_size=1,
        max_size=3
    )
)
def test_nested_clip(tree_dict):
    """Test clip with nested structures."""
    # Convert to JAX arrays
    tree = {k: jnp.array(v, dtype=jnp.float32) for k, v in tree_dict.items()}
    
    clipped = optax.tree.clip(tree, -10.0, 10.0)
    
    # Check all values are clipped
    for k in tree.keys():
        assert jnp.all(clipped[k] >= -10.0 - 1e-6), f"Values below min in key {k}"
        assert jnp.all(clipped[k] <= 10.0 + 1e-6), f"Values above max in key {k}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])