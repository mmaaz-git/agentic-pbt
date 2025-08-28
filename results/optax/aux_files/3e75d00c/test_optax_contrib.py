#!/usr/bin/env python3
"""Property-based tests for optax.contrib module."""

import math
import numpy as np
import jax
import jax.numpy as jnp
from hypothesis import given, assume, strategies as st, settings
import pytest
import optax.contrib
from optax.contrib._complex_valued import (
    _complex_to_real_pair, 
    _real_pair_to_complex,
    SplitRealAndImaginaryArrays
)


# Strategy for generating valid JAX arrays
@st.composite
def jax_arrays(draw, dtype=None, min_dim=1, max_dim=3):
    """Generate JAX arrays with various shapes and dtypes."""
    shape = draw(st.lists(
        st.integers(min_value=1, max_value=5),
        min_size=min_dim,
        max_size=max_dim
    ))
    
    if dtype is None:
        dtype = draw(st.sampled_from([np.float32, np.float64]))
    
    if dtype in [np.complex64, np.complex128]:
        real_part = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=np.prod(shape),
            max_size=np.prod(shape)
        ))
        imag_part = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=np.prod(shape),
            max_size=np.prod(shape)
        ))
        array = np.array(real_part).reshape(shape) + 1j * np.array(imag_part).reshape(shape)
        return jnp.array(array, dtype=dtype)
    else:
        elements = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=np.prod(shape),
            max_size=np.prod(shape)
        ))
        return jnp.array(np.array(elements).reshape(shape), dtype=dtype)


@st.composite 
def gradient_trees(draw):
    """Generate tree structures of gradients for testing."""
    # Simple tree with arrays
    n_arrays = draw(st.integers(min_value=1, max_value=3))
    tree = {}
    for i in range(n_arrays):
        tree[f'param_{i}'] = draw(jax_arrays(dtype=np.float32))
    return tree


# Test 1: normalize() gradient normalization property
@given(gradient_trees())
@settings(max_examples=100)
def test_normalize_unit_norm(gradients):
    """Test that normalize() produces gradients with unit global norm."""
    # Skip if all gradients are zero
    global_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree.leaves(gradients)))
    assume(global_norm > 1e-10)  # Skip zero gradients
    
    # Initialize and apply normalize transformation
    normalize_fn = optax.contrib.normalize()
    state = normalize_fn.init(gradients)
    normalized_grads, _ = normalize_fn.update(gradients, state)
    
    # Check that normalized gradients have unit norm
    normalized_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree.leaves(normalized_grads)))
    
    # Use numerical tolerance for floating point comparison
    assert math.isclose(float(normalized_norm), 1.0, rel_tol=1e-5, abs_tol=1e-6), \
        f"Normalized gradient norm is {normalized_norm}, expected 1.0"


# Test 2: Complex-to-real-pair round-trip property
@given(jax_arrays(dtype=np.complex64))
@settings(max_examples=100)
def test_complex_to_real_round_trip(complex_array):
    """Test that splitting complex to real/imaginary and back preserves values."""
    # Convert complex to real pair
    real_pair = _complex_to_real_pair(complex_array)
    
    # Verify it created a SplitRealAndImaginaryArrays
    assert isinstance(real_pair, SplitRealAndImaginaryArrays)
    
    # Convert back to complex
    recovered = _real_pair_to_complex(real_pair)
    
    # Check arrays are equal
    assert jnp.allclose(complex_array, recovered, rtol=1e-6, atol=1e-8), \
        f"Round-trip failed: original != recovered"


# Test 3: Real arrays pass through unchanged
@given(jax_arrays(dtype=np.float32))
@settings(max_examples=100)
def test_real_arrays_pass_through(real_array):
    """Test that real arrays pass through the complex conversion unchanged."""
    # Convert real array (should pass through)
    result = _complex_to_real_pair(real_array)
    
    # Should be the same array
    assert result is real_array, "Real array should pass through unchanged"
    
    # Convert back (should also pass through)
    recovered = _real_pair_to_complex(real_array)
    assert recovered is real_array, "Real array should pass through unchanged on reverse"


# Test 4: split_real_and_imaginary preserves optimization behavior  
@st.composite
def complex_gradient_trees(draw):
    """Generate trees with mix of real and complex arrays."""
    tree = {}
    n_real = draw(st.integers(min_value=0, max_value=2))
    n_complex = draw(st.integers(min_value=1, max_value=2))
    
    for i in range(n_real):
        tree[f'real_{i}'] = draw(jax_arrays(dtype=np.float32))
    
    for i in range(n_complex):
        tree[f'complex_{i}'] = draw(jax_arrays(dtype=np.complex64))
    
    return tree


@given(complex_gradient_trees())
@settings(max_examples=100)
def test_split_real_imaginary_round_trip(params):
    """Test split_real_and_imaginary wrapper preserves gradient structure."""
    # Create a simple SGD optimizer
    learning_rate = 0.01
    inner_opt = optax.sgd(learning_rate)
    
    # Wrap with split_real_and_imaginary
    wrapped_opt = optax.contrib.split_real_and_imaginary(inner_opt)
    
    # Initialize
    state = wrapped_opt.init(params)
    
    # Create mock gradients (same structure as params)
    gradients = jax.tree.map(lambda x: jnp.ones_like(x) * 0.1, params)
    
    # Apply update
    updates, new_state = wrapped_opt.update(gradients, state, params)
    
    # Check that updates have same structure as params
    def check_structure(p, u):
        assert p.shape == u.shape, f"Shape mismatch: {p.shape} != {u.shape}"
        assert p.dtype == u.dtype, f"Dtype mismatch: {p.dtype} != {u.dtype}"
    
    jax.tree.map(check_structure, params, updates)
    
    # Verify updates are as expected (negative learning rate * gradients for SGD)
    def check_update_values(g, u):
        expected = -learning_rate * g
        assert jnp.allclose(u, expected, rtol=1e-5, atol=1e-7), \
            f"Update values incorrect"
    
    jax.tree.map(check_update_values, gradients, updates)


# Test 5: reduce_on_plateau parameter validation
@given(
    factor=st.floats(min_value=-1.0, max_value=2.0),
    rtol=st.floats(min_value=-1.0, max_value=2.0),
    atol=st.floats(min_value=-1.0, max_value=1.0)
)
def test_reduce_on_plateau_validation(factor, rtol, atol):
    """Test that reduce_on_plateau validates parameters correctly."""
    # Test factor validation
    if factor <= 0.0 or factor >= 1.0:
        with pytest.raises(ValueError, match="Factor must be in the range"):
            optax.contrib.reduce_on_plateau(factor=factor)
    
    # Test rtol/atol validation
    if rtol < 0.0 or atol < 0.0:
        with pytest.raises(ValueError, match="Both rtol and atol must be non-negative"):
            optax.contrib.reduce_on_plateau(factor=0.5, rtol=rtol, atol=atol)
    elif rtol == 0.0 and atol == 0.0:
        with pytest.raises(ValueError, match="At least one of rtol or atol must be positive"):
            optax.contrib.reduce_on_plateau(factor=0.5, rtol=rtol, atol=atol)
    elif rtol > 1.0:
        with pytest.raises(ValueError, match="rtol must be less than or equal to 1.0"):
            optax.contrib.reduce_on_plateau(factor=0.5, rtol=rtol, atol=atol)
    elif 0 < factor < 1.0 and 0 <= rtol <= 1.0 and atol >= 0.0 and not (rtol == 0.0 and atol == 0.0):
        # Should succeed
        opt = optax.contrib.reduce_on_plateau(factor=factor, rtol=rtol, atol=atol)
        assert opt is not None


# Test 6: Check that SAM's normalize handles zero gradients properly
@given(gradient_trees())
def test_normalize_zero_gradient_stability(gradients):
    """Test normalize() handles zero and near-zero gradients gracefully."""
    # Create zero gradients
    zero_grads = jax.tree.map(lambda x: jnp.zeros_like(x), gradients)
    
    # Initialize and apply normalize
    normalize_fn = optax.contrib.normalize()
    state = normalize_fn.init(zero_grads)
    
    # This should not crash - test numerical stability
    normalized, _ = normalize_fn.update(zero_grads, state)
    
    # With zero gradients, result should be NaN or inf (division by zero)
    # Check that it doesn't crash at least
    for g in jax.tree.leaves(normalized):
        # Either all NaN/inf or all zero (depending on implementation)
        assert jnp.all(jnp.isnan(g)) or jnp.all(jnp.isinf(g)) or jnp.all(g == 0), \
            "Unexpected behavior with zero gradients"


if __name__ == "__main__":
    # Run the tests
    print("Running property-based tests for optax.contrib...")
    pytest.main([__file__, "-v"])