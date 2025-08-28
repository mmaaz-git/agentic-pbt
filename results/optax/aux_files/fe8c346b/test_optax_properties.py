#!/usr/bin/env python3
"""Property-based tests for optax functions using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import math
import pytest
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, assume, strategies as st, settings
from hypothesis.extra import numpy as hnp

# Configure JAX
jax.config.update('jax_enable_x64', True)

# Strategy for safe JAX arrays (avoiding NaN/inf)
@st.composite
def safe_floats_array(draw, shape=None, min_value=-1e10, max_value=1e10):
    """Generate safe float arrays without NaN/inf."""
    if shape is None:
        shape = draw(hnp.array_shapes(min_dims=1, max_dims=2, min_side=1, max_side=10))
    return draw(hnp.arrays(
        dtype=np.float32,
        shape=shape,
        elements=st.floats(
            allow_nan=False, 
            allow_infinity=False,
            min_value=min_value,
            max_value=max_value
        )
    ))

# Test 1: safe_increment never overflows
@given(
    count=st.one_of(
        st.integers(min_value=-2147483648, max_value=2147483647),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_safe_increment_no_overflow(count):
    """Test that safe_increment never overflows, stays at max."""
    count_jax = jnp.asarray(count)
    result = optax.safe_increment(count_jax)
    
    # Check it doesn't overflow
    assert not jnp.isnan(result)
    assert not jnp.isinf(result)
    
    # Check behavior at boundaries
    if jnp.issubdtype(count_jax.dtype, jnp.integer):
        max_val = jnp.iinfo(count_jax.dtype).max
        if count == max_val:
            # Should stay at max
            assert result == max_val
        else:
            # Should increment by 1
            assert result == count + 1
    else:
        max_val = jnp.finfo(count_jax.dtype).max
        if count >= max_val - 1:
            # Should stay at max
            assert result == max_val
        else:
            # Should increment by 1
            assert math.isclose(float(result), count + 1, rel_tol=1e-7)

# Test 2: safe_norm always returns >= min_norm
@given(
    x=safe_floats_array(),
    min_norm=st.floats(min_value=1e-10, max_value=1.0, allow_nan=False, allow_infinity=False)
)
def test_safe_norm_invariant(x, min_norm):
    """Test that safe_norm always returns a value >= min_norm."""
    x_jax = jnp.asarray(x)
    result = optax.safe_norm(x_jax, min_norm)
    
    # Main invariant: result >= min_norm
    assert result >= min_norm - 1e-7, f"Result {result} < min_norm {min_norm}"
    
    # Additional check: if actual norm > min_norm, should return actual norm
    actual_norm = jnp.linalg.norm(x_jax)
    if actual_norm > min_norm + 1e-7:
        assert math.isclose(float(result), float(actual_norm), rel_tol=1e-6)

# Test 3: abs_sq for real numbers equals x*x
@given(x=safe_floats_array(min_value=-1e5, max_value=1e5))
def test_abs_sq_real(x):
    """Test that abs_sq(x) == x*x for real arrays."""
    from optax._src.numerics import abs_sq
    
    x_jax = jnp.asarray(x)
    result = abs_sq(x_jax)
    expected = x_jax * x_jax
    
    # Should be element-wise equal
    np.testing.assert_allclose(result, expected, rtol=1e-6, atol=1e-10)
    
    # Should always be non-negative
    assert jnp.all(result >= 0)

# Test 4: abs_sq for complex numbers
@given(
    real=safe_floats_array(shape=(5,), min_value=-100, max_value=100),
    imag=safe_floats_array(shape=(5,), min_value=-100, max_value=100)
)
def test_abs_sq_complex(real, imag):
    """Test abs_sq for complex numbers: abs_sq(z) = |z|^2."""
    from optax._src.numerics import abs_sq
    
    z = jnp.asarray(real + 1j * imag)
    result = abs_sq(z)
    
    # abs_sq(z) should equal |z|^2 = real^2 + imag^2
    expected = real**2 + imag**2
    np.testing.assert_allclose(result, expected, rtol=1e-6)
    
    # Result should always be real and non-negative
    assert jnp.all(jnp.isreal(result))
    assert jnp.all(result >= 0)

# Test 5: incremental_update implements correct polyak averaging
@given(
    new_val=safe_floats_array(shape=(3, 3)),
    old_val=safe_floats_array(shape=(3, 3)),
    step_size=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
)
def test_incremental_update_polyak(new_val, old_val, step_size):
    """Test incremental_update implements: step_size*new + (1-step_size)*old."""
    new_jax = jnp.asarray(new_val)
    old_jax = jnp.asarray(old_val)
    
    result = optax.incremental_update(new_jax, old_jax, step_size)
    expected = step_size * new_jax + (1.0 - step_size) * old_jax
    
    np.testing.assert_allclose(result, expected, rtol=1e-6, atol=1e-10)
    
    # Special cases
    if step_size == 0.0:
        np.testing.assert_array_equal(result, old_jax)
    elif step_size == 1.0:
        np.testing.assert_array_equal(result, new_jax)

# Test 6: apply_updates adds updates to params correctly
@given(
    params=safe_floats_array(shape=(5,)),
    updates=safe_floats_array(shape=(5,), min_value=-10, max_value=10)
)
def test_apply_updates_addition(params, updates):
    """Test that apply_updates correctly adds updates to params."""
    params_jax = jnp.asarray(params, dtype=jnp.float32)
    updates_jax = jnp.asarray(updates, dtype=jnp.float32)
    
    result = optax.apply_updates(params_jax, updates_jax)
    expected = params_jax + updates_jax
    
    # Check addition is correct
    np.testing.assert_allclose(result, expected, rtol=1e-6)
    
    # Check dtype is preserved
    assert result.dtype == params_jax.dtype

# Test 7: apply_updates handles None correctly
@given(
    updates=safe_floats_array(shape=(3,))
)
def test_apply_updates_none_handling(updates):
    """Test that apply_updates handles None params correctly."""
    updates_jax = jnp.asarray(updates)
    
    # When params is None, result should be None
    result = optax.apply_updates(None, updates_jax)
    assert result is None
    
    # Test with tree structure containing None
    params_tree = {'a': jnp.array([1.0, 2.0]), 'b': None}
    updates_tree = {'a': jnp.array([0.1, 0.2]), 'b': jnp.array([0.3])}
    
    result_tree = optax.apply_updates(params_tree, updates_tree)
    assert result_tree['b'] is None
    np.testing.assert_allclose(result_tree['a'], params_tree['a'] + updates_tree['a'])

# Test 8: safe_root_mean_squares invariant
@given(
    x=safe_floats_array(),
    min_rms=st.floats(min_value=1e-10, max_value=1.0, allow_nan=False)
)
def test_safe_root_mean_squares_invariant(x, min_rms):
    """Test that safe_root_mean_squares always returns >= min_rms."""
    x_jax = jnp.asarray(x)
    result = optax.safe_root_mean_squares(x_jax, min_rms)
    
    # Main invariant
    assert result >= min_rms - 1e-7
    
    # Check correctness when RMS > min_rms
    from optax._src.numerics import abs_sq
    actual_rms = jnp.sqrt(jnp.mean(abs_sq(x_jax)))
    if actual_rms > min_rms + 1e-7:
        assert math.isclose(float(result), float(actual_rms), rel_tol=1e-6)

# Test 9: global_norm computes correct L2 norm
@given(
    x=safe_floats_array(shape=(5,)),
    y=safe_floats_array(shape=(3, 3))
)
def test_global_norm_correctness(x, y):
    """Test that global_norm computes the correct L2 norm across tree."""
    tree = {'a': jnp.asarray(x), 'b': jnp.asarray(y)}
    
    result = optax.global_norm(tree)
    
    # Manually compute expected norm
    expected = jnp.sqrt(jnp.sum(x**2) + jnp.sum(y**2))
    
    assert math.isclose(float(result), float(expected), rel_tol=1e-6)
    assert result >= 0  # Norm is always non-negative

# Test 10: periodic_update only updates at right intervals
@given(
    new_val=safe_floats_array(shape=(3,)),
    old_val=safe_floats_array(shape=(3,)),
    steps=st.integers(min_value=0, max_value=100),
    update_period=st.integers(min_value=1, max_value=10)
)
def test_periodic_update_timing(new_val, old_val, steps, update_period):
    """Test that periodic_update only updates when steps % period == 0."""
    new_jax = jnp.asarray(new_val)
    old_jax = jnp.asarray(old_val)
    steps_jax = jnp.asarray(steps)
    
    result = optax.periodic_update(new_jax, old_jax, steps_jax, update_period)
    
    if steps % update_period == 0:
        # Should return new values
        np.testing.assert_array_equal(result, new_jax)
    else:
        # Should return old values
        np.testing.assert_array_equal(result, old_jax)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])