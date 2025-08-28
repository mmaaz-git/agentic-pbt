#!/usr/bin/env python3
"""Property-based tests for optax.perturbations module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import math
import jax
import jax.numpy as jnp
import numpy as np
import optax.perturbations as pert
from optax.perturbations._make_pert import _magicbox
from hypothesis import given, strategies as st, settings, assume
import pytest

# Disable JAX's 64-bit mode warnings
jax.config.update("jax_enable_x64", False)

# Strategy for reasonable float arrays
reasonable_floats = st.floats(
    min_value=-1e6, 
    max_value=1e6, 
    allow_nan=False, 
    allow_infinity=False,
    width=32
)

array_shapes = st.tuples(
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=10)
)

# Test 1: Normal.log_prob mathematical correctness
@given(
    st.lists(
        reasonable_floats,
        min_size=1,
        max_size=100
    )
)
def test_normal_log_prob_formula(values):
    """Test that Normal.log_prob(x) == -0.5 * x^2"""
    normal = pert.Normal()
    x = jnp.array(values)
    
    result = normal.log_prob(x)
    expected = -0.5 * x**2
    
    # Check shape preservation
    assert result.shape == expected.shape, f"Shape mismatch: {result.shape} != {expected.shape}"
    
    # Check values
    np.testing.assert_allclose(result, expected, rtol=1e-5, atol=1e-7)

# Test 2: Gumbel.log_prob mathematical correctness
@given(
    st.lists(
        st.floats(
            min_value=-10,  # Avoid extremely negative values that could cause exp overflow
            max_value=10,
            allow_nan=False,
            allow_infinity=False,
            width=32
        ),
        min_size=1,
        max_size=100
    )
)
def test_gumbel_log_prob_formula(values):
    """Test that Gumbel.log_prob(x) == -x - exp(-x)"""
    gumbel = pert.Gumbel()
    x = jnp.array(values)
    
    result = gumbel.log_prob(x)
    expected = -x - jnp.exp(-x)
    
    # Check shape preservation
    assert result.shape == expected.shape, f"Shape mismatch: {result.shape} != {expected.shape}"
    
    # Check values
    np.testing.assert_allclose(result, expected, rtol=1e-5, atol=1e-7)

# Test 3: Distribution sampling shape properties
@given(
    array_shapes,
    st.sampled_from([pert.Normal(), pert.Gumbel()]),
    st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=50)
def test_distribution_sample_shapes(shape, distribution, seed):
    """Test that distributions produce samples with correct shapes."""
    key = jax.random.key(seed)
    
    # Test sampling with shape
    samples = distribution.sample(key, shape)
    assert samples.shape == shape, f"Expected shape {shape}, got {samples.shape}"
    
    # Check samples are finite
    assert jnp.all(jnp.isfinite(samples)), "Samples contain NaN or inf values"
    
    # Test empty shape (scalar)
    key2 = jax.random.split(key)[0]
    scalar_sample = distribution.sample(key2, ())
    assert scalar_sample.shape == (), f"Expected scalar shape (), got {scalar_sample.shape}"
    assert jnp.isfinite(scalar_sample), "Scalar sample is NaN or inf"

# Test 4: Make_perturbed_fun shape preservation
@given(
    st.lists(
        reasonable_floats,
        min_size=2,
        max_size=10
    ),
    st.integers(min_value=10, max_value=100),
    st.floats(min_value=0.01, max_value=1.0),
    st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=20, deadline=10000)
def test_make_perturbed_fun_shape_preservation(values, num_samples, sigma, seed):
    """Test that make_perturbed_fun preserves output shapes."""
    x = jnp.array(values)
    key = jax.random.key(seed)
    
    # Simple test function that changes shape
    def test_func(x):
        return jnp.stack([jnp.sum(x), jnp.mean(x), jnp.max(x)])
    
    perturbed_func = pert.make_perturbed_fun(
        test_func, 
        num_samples=num_samples,
        sigma=sigma,
        noise=pert.Normal()
    )
    
    original_output = test_func(x)
    perturbed_output = perturbed_func(key, x)
    
    # Check shape preservation
    assert perturbed_output.shape == original_output.shape, \
        f"Shape not preserved: {perturbed_output.shape} != {original_output.shape}"
    
    # Check outputs are finite
    assert jnp.all(jnp.isfinite(perturbed_output)), "Perturbed output contains NaN or inf"

# Test 5: Make_perturbed_fun with sigma approaching 0
@given(
    st.lists(
        st.floats(
            min_value=-10,
            max_value=10,
            allow_nan=False,
            allow_infinity=False,
            width=32
        ),
        min_size=2,
        max_size=10
    ),
    st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=20, deadline=10000)
def test_make_perturbed_fun_small_sigma(values, seed):
    """Test that with very small sigma, perturbed function approximates original."""
    x = jnp.array(values)
    key = jax.random.key(seed)
    
    # Simple smooth test function
    def smooth_func(x):
        return jnp.sum(x**2) + jnp.mean(jnp.cos(x))
    
    # Test with very small sigma
    perturbed_func = pert.make_perturbed_fun(
        smooth_func,
        num_samples=1000,
        sigma=1e-6,  # Very small sigma
        noise=pert.Normal()
    )
    
    original_output = smooth_func(x)
    perturbed_output = perturbed_func(key, x)
    
    # With tiny sigma, outputs should be very close
    np.testing.assert_allclose(
        perturbed_output, 
        original_output, 
        rtol=1e-2,  # 1% relative tolerance
        atol=1e-3   # Small absolute tolerance
    )

# Test 6: MagicBox operator property
@given(
    st.floats(
        min_value=-10,
        max_value=10,
        allow_nan=False,
        allow_infinity=False
    )
)
def test_magicbox_property(x):
    """Test the magicbox operator exp(x - stop_gradient(x))."""
    x_jax = jnp.array(x)
    result = _magicbox(x_jax)
    
    # Without gradients flowing, stop_gradient(x) = x
    # So _magicbox(x) = exp(x - x) = exp(0) = 1
    # But with JAX's implementation, we need to check the formula
    expected = jnp.exp(x_jax - jax.lax.stop_gradient(x_jax))
    
    np.testing.assert_allclose(result, expected, rtol=1e-6, atol=1e-8)
    
    # When no gradients, this should be 1
    assert jnp.allclose(result, 1.0), f"MagicBox({x}) = {result}, expected ~1.0"

# Test 7: Test tree structure handling
@given(
    st.lists(reasonable_floats, min_size=2, max_size=5),
    st.lists(reasonable_floats, min_size=2, max_size=5),
    st.integers(min_value=10, max_value=100),
    st.floats(min_value=0.01, max_value=1.0),
    st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=10, deadline=20000)
def test_make_perturbed_fun_with_trees(list1, list2, num_samples, sigma, seed):
    """Test that make_perturbed_fun handles tree-structured inputs correctly."""
    # Create a tree structure
    x_tree = {
        'array1': jnp.array(list1),
        'nested': {
            'array2': jnp.array(list2)
        }
    }
    
    key = jax.random.key(seed)
    
    # Function that operates on tree
    def tree_func(tree):
        return {
            'sum': jnp.sum(tree['array1']) + jnp.sum(tree['nested']['array2']),
            'mean': jnp.mean(tree['array1'])
        }
    
    perturbed_func = pert.make_perturbed_fun(
        tree_func,
        num_samples=num_samples,
        sigma=sigma,
        noise=pert.Normal()
    )
    
    original_output = tree_func(x_tree)
    perturbed_output = perturbed_func(key, x_tree)
    
    # Check structure preservation
    assert set(perturbed_output.keys()) == set(original_output.keys()), \
        "Tree structure not preserved"
    
    # Check shapes match
    for key in original_output:
        assert perturbed_output[key].shape == original_output[key].shape, \
            f"Shape mismatch for key {key}"
        assert jnp.isfinite(perturbed_output[key]).all(), \
            f"Non-finite values in output for key {key}"

# Test 8: Test that both Normal and Gumbel produce valid samples across dtypes
@given(
    st.sampled_from([jnp.float32, jnp.float64]),
    st.sampled_from([pert.Normal(), pert.Gumbel()]),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=2**31-1)
)
def test_distribution_dtype_handling(dtype, distribution, size, seed):
    """Test that distributions handle different dtypes correctly."""
    key = jax.random.key(seed)
    shape = (size,)
    
    samples = distribution.sample(key, shape, dtype=dtype)
    
    # Check dtype
    assert samples.dtype == dtype, f"Expected dtype {dtype}, got {samples.dtype}"
    
    # Check shape
    assert samples.shape == shape, f"Expected shape {shape}, got {samples.shape}"
    
    # Check finite
    assert jnp.all(jnp.isfinite(samples)), "Samples contain NaN or inf"
    
    # Test log_prob works on these samples
    log_probs = distribution.log_prob(samples)
    assert log_probs.shape == samples.shape, "log_prob shape mismatch"
    assert jnp.all(jnp.isfinite(log_probs)), "log_prob contains NaN or inf"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])