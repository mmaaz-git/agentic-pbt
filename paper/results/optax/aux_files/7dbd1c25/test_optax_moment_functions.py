"""Property-based tests for optax.tree moment update functions."""

import math
import jax.numpy as jnp
import numpy as np
import optax.tree
from hypothesis import assume, given, settings, strategies as st


def safe_floats():
    """Safe float strategy."""
    return st.floats(
        allow_nan=False,
        allow_infinity=False,
        min_value=-1e4,
        max_value=1e4,
        width=32
    )


def decay_strategy():
    """Generate valid decay values (between 0 and 1)."""
    return st.floats(min_value=0.0, max_value=1.0, exclude_min=False, exclude_max=False)


@given(
    st.lists(safe_floats(), min_size=1, max_size=5),
    st.lists(safe_floats(), min_size=1, max_size=5),
    st.integers(min_value=1, max_value=4)
)
def test_update_moment_decay_zero(updates, moments, order):
    """Test update_moment with decay=0 returns updates**order."""
    assume(len(updates) == len(moments))
    
    updates_tree = jnp.array(updates, dtype=jnp.float32)
    moments_tree = jnp.array(moments, dtype=jnp.float32)
    
    result = optax.tree.update_moment(updates_tree, moments_tree, decay=0.0, order=order)
    expected = updates_tree ** order
    
    assert jnp.allclose(result, expected, rtol=1e-5, atol=1e-6), \
        f"update_moment with decay=0 failed: {result} != {expected}"


@given(
    st.lists(safe_floats(), min_size=1, max_size=5),
    st.lists(safe_floats(), min_size=1, max_size=5),
    st.integers(min_value=1, max_value=4)
)
def test_update_moment_decay_one(updates, moments, order):
    """Test update_moment with decay=1 returns moments unchanged."""
    assume(len(updates) == len(moments))
    
    updates_tree = jnp.array(updates, dtype=jnp.float32)
    moments_tree = jnp.array(moments, dtype=jnp.float32)
    
    result = optax.tree.update_moment(updates_tree, moments_tree, decay=1.0, order=order)
    
    assert jnp.allclose(result, moments_tree, rtol=1e-5, atol=1e-6), \
        f"update_moment with decay=1 didn't return moments: {result} != {moments_tree}"


@given(
    st.lists(safe_floats(), min_size=1, max_size=5),
    decay_strategy().filter(lambda x: 0.1 <= x <= 0.99),
    st.integers(min_value=1, max_value=100)
)
def test_bias_correction_properties(moments, decay, count):
    """Test bias correction properties."""
    moments_tree = jnp.array(moments, dtype=jnp.float32)
    
    # Apply bias correction
    corrected = optax.tree.bias_correction(moments_tree, decay, count)
    
    # Expected correction factor
    correction_factor = 1.0 / (1.0 - decay ** count)
    expected = moments_tree * correction_factor
    
    assert jnp.allclose(corrected, expected, rtol=1e-4, atol=1e-6), \
        f"Bias correction failed: {corrected} != {expected}"
    
    # Check that correction factor increases with count (for decay < 1)
    if count > 1 and decay < 0.999:
        corrected_prev = optax.tree.bias_correction(moments_tree, decay, count - 1)
        # The absolute correction should be larger for higher count
        assert jnp.all(jnp.abs(corrected) >= jnp.abs(corrected_prev) - 1e-6), \
            f"Bias correction not monotonic"


@given(
    st.lists(safe_floats(), min_size=1, max_size=5),
    decay_strategy()
)
def test_bias_correction_infinite_count(moments, decay):
    """Test that bias correction approaches no-op as count → ∞."""
    assume(decay < 0.999)  # For decay very close to 1, need extremely large count
    
    moments_tree = jnp.array(moments, dtype=jnp.float32)
    
    # Use a large count to simulate infinity
    large_count = 1000
    corrected = optax.tree.bias_correction(moments_tree, decay, large_count)
    
    # Should be very close to original moments (within 1% for reasonable decay)
    assert jnp.allclose(corrected, moments_tree, rtol=0.01, atol=1e-4), \
        f"Bias correction doesn't approach no-op for large count"


@given(
    st.lists(safe_floats(), min_size=1, max_size=5),
    st.lists(safe_floats(), min_size=1, max_size=5),
    decay_strategy(),
    st.floats(min_value=1e-8, max_value=1.0)
)
def test_update_infinity_moment_properties(updates, moments, decay, eps):
    """Test update_infinity_moment properties."""
    assume(len(updates) == len(moments))
    
    updates_tree = jnp.array(updates, dtype=jnp.float32)
    moments_tree = jnp.array(moments, dtype=jnp.float32)
    
    result = optax.tree.update_infinity_moment(updates_tree, moments_tree, decay, eps)
    
    # Result should always be >= eps
    assert jnp.all(result >= eps - 1e-7), f"Result less than eps: min={jnp.min(result)}, eps={eps}"
    
    # For decay=0, should return |updates| + eps
    if decay == 0:
        expected = jnp.abs(updates_tree) + eps
        assert jnp.allclose(result, expected, rtol=1e-5, atol=1e-6), \
            f"With decay=0, didn't get |updates| + eps"


@given(
    st.lists(safe_floats(), min_size=1, max_size=5),
    st.lists(safe_floats(), min_size=1, max_size=5),
    decay_strategy(),
    st.integers(min_value=1, max_value=4)
)
def test_update_moment_idempotence(updates, initial_moments, decay, order):
    """Test that repeatedly applying update_moment converges."""
    assume(len(updates) == len(initial_moments))
    assume(0.1 <= decay <= 0.9)  # Need reasonable decay for convergence
    
    updates_tree = jnp.array(updates, dtype=jnp.float32)
    moments = jnp.array(initial_moments, dtype=jnp.float32)
    
    # Apply update_moment multiple times with same updates
    for _ in range(100):
        moments = optax.tree.update_moment(updates_tree, moments, decay, order)
    
    # Should converge to updates**order
    expected_limit = updates_tree ** order
    
    # Check convergence (with reasonable tolerance for float32)
    assert jnp.allclose(moments, expected_limit, rtol=0.01, atol=0.01), \
        f"update_moment didn't converge to expected value"


@given(
    st.lists(st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False), 
             min_size=1, max_size=5),
    decay_strategy().filter(lambda x: 0.5 <= x <= 0.99)
)
def test_bias_correction_division_by_zero(moments, decay):
    """Test bias correction with count=0 (edge case)."""
    moments_tree = jnp.array(moments, dtype=jnp.float32)
    
    # When count=0, we have 1 - decay^0 = 1 - 1 = 0, which would cause division by zero
    # The function should handle this gracefully
    try:
        result = optax.tree.bias_correction(moments_tree, decay, count=0)
        # If it doesn't raise an error, check if result is inf (as expected from division by 0)
        assert jnp.all(jnp.isinf(result)), f"Expected inf from division by zero, got {result}"
    except ZeroDivisionError:
        # This is also acceptable behavior
        pass
    except Exception as e:
        # Any other exception is unexpected
        assert False, f"Unexpected exception: {e}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])