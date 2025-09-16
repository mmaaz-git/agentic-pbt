import math
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test for potential numerical issues with clip_by_global_norm
@given(
    scale=st.sampled_from([1e-30, 1e30, 1e-10, 1e10]),
    max_norm=st.floats(min_value=1e-10, max_value=1e10)
)
@settings(max_examples=200, deadline=5000)
def test_clip_by_global_norm_scale_invariance(scale, max_norm):
    """Test that clip_by_global_norm handles different scales correctly."""
    tx = optax.transforms.clip_by_global_norm(max_norm)
    
    # Create gradients at different scales
    base_grads = jnp.array([1.0, 2.0, 3.0])
    grads = {'x': base_grads * scale}
    params = {'x': jnp.zeros(3)}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Calculate actual global norm after clipping
    actual_norm = jnp.linalg.norm(updates['x'])
    
    # Original norm
    orig_norm = jnp.linalg.norm(grads['x'])
    
    if orig_norm > max_norm:
        # Should be clipped to max_norm
        assert actual_norm <= max_norm * 1.01, f"Norm {actual_norm} exceeds max {max_norm}"
        # Check direction is preserved
        if scale != 0:
            direction_orig = grads['x'] / (orig_norm + 1e-10)
            direction_clipped = updates['x'] / (actual_norm + 1e-10)
            np.testing.assert_allclose(direction_orig, direction_clipped, rtol=1e-5)
    else:
        # Should be unchanged
        np.testing.assert_allclose(updates['x'], grads['x'], rtol=1e-6)


# Test trace with nesterov momentum
@given(
    decay=st.floats(min_value=0.5, max_value=0.99),
    nesterov=st.booleans()
)
@settings(max_examples=100, deadline=5000)
def test_trace_nesterov_difference(decay, nesterov):
    """Test that nesterov=True produces different results than nesterov=False."""
    tx_regular = optax.transforms.trace(decay=decay, nesterov=False)
    tx_nesterov = optax.transforms.trace(decay=decay, nesterov=True)
    
    params = {'x': jnp.zeros(3)}
    grads = {'x': jnp.array([1.0, 2.0, 3.0])}
    
    # Initialize and apply first update
    state_regular = tx_regular.init(params)
    state_nesterov = tx_nesterov.init(params)
    
    updates_regular1, state_regular = tx_regular.update(grads, state_regular)
    updates_nesterov1, state_nesterov = tx_nesterov.update(grads, state_nesterov)
    
    # First update should be the same (both start from zero trace)
    np.testing.assert_allclose(updates_regular1['x'], updates_nesterov1['x'], rtol=1e-6)
    
    # Second update should differ if nesterov is used
    updates_regular2, _ = tx_regular.update(grads, state_regular)
    updates_nesterov2, _ = tx_nesterov.update(grads, state_nesterov)
    
    if nesterov and decay > 0:
        # Nesterov should produce different results on second iteration
        diff = jnp.sum(jnp.abs(updates_regular2['x'] - updates_nesterov2['x']))
        assert diff > 1e-6, "Nesterov didn't produce different results"


# Test apply_if_finite consecutive error handling
@given(
    num_errors=st.integers(min_value=1, max_value=10),
    max_consecutive=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=5000)
def test_apply_if_finite_consecutive_errors(num_errors, max_consecutive):
    """Test apply_if_finite handles consecutive errors correctly."""
    inner_tx = optax.identity()
    tx = optax.transforms.apply_if_finite(inner_tx, max_consecutive_errors=max_consecutive)
    
    params = {'x': jnp.array([1.0, 2.0])}
    state = tx.init(params)
    
    # Apply num_errors updates with NaN
    nan_grads = {'x': jnp.array([np.nan, 1.0])}
    normal_grads = {'x': jnp.array([1.0, 1.0])}
    
    for i in range(num_errors):
        updates, state = tx.update(nan_grads, state)
        # Should return zeros for non-finite gradients
        assert jnp.all(updates['x'] == 0), f"Non-zero updates with NaN at step {i+1}"
        
        if i < max_consecutive:
            # Should still be usable
            assert state.total_notfinite <= max_consecutive
        else:
            # Should have hit the limit
            assert state.total_notfinite >= max_consecutive
    
    # After normal gradient, counter should reset if not exceeded
    if num_errors < max_consecutive:
        updates, state = tx.update(normal_grads, state)
        np.testing.assert_allclose(updates['x'], normal_grads['x'])
        assert state.total_notfinite == 0, "Counter not reset after finite gradient"


# Test interaction between zero_nans and clip
@given(
    has_nan=st.booleans(),
    clip_value=st.floats(min_value=0.1, max_value=10)
)
@settings(max_examples=100, deadline=5000)
def test_zero_nans_then_clip(has_nan, clip_value):
    """Test chaining zero_nans before clip handles NaN correctly."""
    tx = optax.chain(
        optax.transforms.zero_nans(),
        optax.transforms.clip(clip_value)
    )
    
    params = {'x': jnp.zeros(3)}
    
    if has_nan:
        grads = {'x': jnp.array([np.nan, 20.0, -20.0])}
    else:
        grads = {'x': jnp.array([5.0, 20.0, -20.0])}
    
    state = tx.init(params)
    updates, new_state = tx.update(grads, state)
    
    # Check no NaN in output
    assert not jnp.any(jnp.isnan(updates['x'])), "NaN in output after zero_nans + clip"
    
    # Check clipping is applied
    assert jnp.all(jnp.abs(updates['x']) <= clip_value * 1.01), "Values not clipped"
    
    if has_nan:
        # First element should be 0 (was NaN)
        assert updates['x'][0] == 0, "NaN not replaced with 0"
        # State should record NaN was found
        assert new_state[0].found_nan['x'] == True


# Test keep_params_nonnegative with zero params
@given(
    negative_update=st.floats(min_value=-10, max_value=-0.1)
)
@settings(max_examples=100, deadline=5000)
def test_keep_params_nonnegative_at_zero(negative_update):
    """Test keep_params_nonnegative when params are exactly zero."""
    tx = optax.transforms.keep_params_nonnegative()
    
    # Start with params at zero
    params = {'x': jnp.array([0.0, 0.0])}
    grads = {'x': jnp.array([negative_update, negative_update])}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state, params)
    
    # Updates should be clipped to zero (can't go negative from zero)
    assert jnp.all(updates['x'] == 0), f"Negative updates from zero not blocked"
    
    # Positive updates from zero should work
    pos_grads = {'x': jnp.array([1.0, 1.0])}
    pos_updates, _ = tx.update(pos_grads, state, params)
    np.testing.assert_allclose(pos_updates['x'], pos_grads['x'])