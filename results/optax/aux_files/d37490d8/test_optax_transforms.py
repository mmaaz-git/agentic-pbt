import math
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, assume, settings
import pytest


# Helper strategies for generating JAX arrays
@st.composite
def jax_arrays(draw, shape=None, min_value=-1e6, max_value=1e6, allow_nan=False):
    """Generate JAX arrays with specified properties."""
    if shape is None:
        shape = draw(st.tuples(st.integers(1, 10)))
    
    elements = st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=allow_nan,
        allow_infinity=False
    )
    
    array = draw(st.lists(elements, min_size=int(np.prod(shape)), max_size=int(np.prod(shape))))
    return jnp.array(array).reshape(shape)


@st.composite
def pytree_params(draw, max_depth=3, max_keys=5):
    """Generate pytree structures similar to neural network parameters."""
    if max_depth == 0:
        return draw(jax_arrays())
    
    num_keys = draw(st.integers(1, max_keys))
    keys = draw(st.lists(
        st.text(alphabet='abcdefghij', min_size=1, max_size=5),
        min_size=num_keys,
        max_size=num_keys,
        unique=True
    ))
    
    result = {}
    for key in keys:
        if draw(st.booleans()):
            result[key] = draw(jax_arrays())
        else:
            result[key] = draw(pytree_params(max_depth - 1, max_keys))
    
    return result


# Test 1: clip invariant
@given(
    params=pytree_params(max_depth=2, max_keys=3),
    max_delta=st.floats(min_value=1e-6, max_value=1e3)
)
@settings(max_examples=100, deadline=5000)
def test_clip_bounds_invariant(params, max_delta):
    """Test that clip keeps all values within [-max_delta, +max_delta]."""
    tx = optax.transforms.clip(max_delta)
    
    # Generate gradients with larger values to test clipping
    grads = jax.tree.map(lambda x: x * 10, params)
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Check that all updates are within bounds
    def check_bounds(x):
        assert jnp.all(jnp.abs(x) <= max_delta + 1e-7), f"Found values outside bounds: {x}"
    
    jax.tree.map(check_bounds, updates)


# Test 2: clip_by_global_norm invariant
@given(
    params=pytree_params(max_depth=2, max_keys=3),
    max_norm=st.floats(min_value=1e-6, max_value=1e3)
)
@settings(max_examples=100, deadline=5000)
def test_clip_by_global_norm_invariant(params, max_norm):
    """Test that clip_by_global_norm keeps global norm <= max_norm."""
    tx = optax.transforms.clip_by_global_norm(max_norm)
    
    # Generate gradients with potentially large norms
    grads = jax.tree.map(lambda x: x * 100, params)
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Calculate global norm of updates
    sum_of_squares = sum(
        jnp.sum(jnp.square(x)) for x in jax.tree.leaves(updates)
    )
    global_norm = jnp.sqrt(sum_of_squares)
    
    assert global_norm <= max_norm * (1 + 1e-6), f"Global norm {global_norm} exceeds {max_norm}"


# Test 3: zero_nans property
@given(
    shape=st.tuples(st.integers(1, 10), st.integers(1, 10))
)
@settings(max_examples=100, deadline=5000)
def test_zero_nans_replaces_nans(shape):
    """Test that zero_nans replaces NaN values with 0 and preserves others."""
    tx = optax.transforms.zero_nans()
    
    # Create gradients with mix of NaN and normal values
    normal_values = np.random.randn(*shape)
    nan_mask = np.random.random(shape) < 0.3  # 30% NaN
    grads_array = normal_values.copy()
    grads_array[nan_mask] = np.nan
    
    params = {'layer': jnp.zeros(shape)}
    grads = {'layer': jnp.array(grads_array)}
    
    state = tx.init(params)
    updates, new_state = tx.update(grads, state)
    
    # Check NaNs are replaced with 0
    result = updates['layer']
    assert not jnp.any(jnp.isnan(result)), "NaN values still present after zero_nans"
    
    # Check non-NaN values are preserved
    non_nan_mask = ~nan_mask
    if np.any(non_nan_mask):
        np.testing.assert_allclose(
            result[non_nan_mask],
            normal_values[non_nan_mask],
            rtol=1e-7
        )
    
    # Check zeros where NaNs were
    assert jnp.all(result[nan_mask] == 0), "NaN values not replaced with 0"


# Test 4: keep_params_nonnegative property
@given(
    params_values=jax_arrays(shape=(5, 5), min_value=0, max_value=10),
    update_values=jax_arrays(shape=(5, 5), min_value=-15, max_value=5)
)
@settings(max_examples=100, deadline=5000)
def test_keep_params_nonnegative_invariant(params_values, update_values):
    """Test that keep_params_nonnegative ensures params + updates >= 0."""
    tx = optax.transforms.keep_params_nonnegative()
    
    params = {'weights': params_values}
    grads = {'weights': update_values}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state, params)
    
    # Check that params + updates >= 0
    new_params = params['weights'] + updates['weights']
    assert jnp.all(new_params >= -1e-7), f"Negative values found: {jnp.min(new_params)}"


# Test 5: Chain composability
@given(
    params=pytree_params(max_depth=2, max_keys=2),
    max_delta1=st.floats(min_value=0.1, max_value=10),
    max_delta2=st.floats(min_value=0.1, max_value=10)
)
@settings(max_examples=100, deadline=5000)
def test_chain_composability(params, max_delta1, max_delta2):
    """Test that chain(f, g) is equivalent to applying f then g."""
    # Use the smaller max_delta for the expected result
    effective_max_delta = min(max_delta1, max_delta2)
    
    # Create two clip transformations
    tx1 = optax.transforms.clip(max_delta1)
    tx2 = optax.transforms.clip(max_delta2)
    
    # Create chained transformation
    tx_chain = optax.chain(tx1, tx2)
    
    # Generate test gradients
    grads = jax.tree.map(lambda x: x * 5, params)
    
    # Apply chain
    state_chain = tx_chain.init(params)
    updates_chain, _ = tx_chain.update(grads, state_chain)
    
    # Apply individually
    state1 = tx1.init(params)
    updates1, _ = tx1.update(grads, state1)
    state2 = tx2.init(params)
    updates2, _ = tx2.update(updates1, state2)
    
    # Compare results
    def assert_close(x, y):
        np.testing.assert_allclose(x, y, rtol=1e-7, atol=1e-7)
    
    jax.tree.map(assert_close, updates_chain, updates2)


# Test 6: EMA basic property - output changes gradually
@given(
    value=st.floats(min_value=-100, max_value=100, allow_nan=False),
    decay=st.floats(min_value=0.5, max_value=0.95)
)
@settings(max_examples=100, deadline=5000)
def test_ema_basic_property(value, decay):
    """Test that EMA produces intermediate values between initial and target."""
    tx = optax.transforms.ema(decay=decay, debias=True)
    
    params = {'x': jnp.zeros(3)}
    grads = {'x': jnp.array([value, value, value])}
    
    state = tx.init(params)
    
    # First update should be between 0 and value
    updates1, state = tx.update(grads, state)
    
    # EMA should produce values between 0 and the gradient
    if value != 0:
        for v in updates1['x']:
            assert abs(v) <= abs(value) * 1.1, f"EMA value {v} exceeds gradient {value}"
    
    # Apply again - should move closer to value
    updates2, state = tx.update(grads, state)
    
    # Second update should be closer to value than first
    if value != 0 and decay > 0.5:
        # For non-zero values and reasonable decay, second should be larger/closer
        if value > 0:
            assert jnp.all(updates2['x'] >= updates1['x'] * 0.95)
        else:
            assert jnp.all(updates2['x'] <= updates1['x'] * 0.95)


# Test 7: clip_by_block_rms clips blocks correctly
@given(
    values=jax_arrays(shape=(6, 4), min_value=-10, max_value=10),
    threshold=st.floats(min_value=0.1, max_value=5.0)
)
@settings(max_examples=100, deadline=5000)
def test_clip_by_block_rms(values, threshold):
    """Test that clip_by_block_rms limits the RMS of blocks."""
    tx = optax.transforms.clip_by_block_rms(threshold)
    
    params = {'weights': jnp.zeros_like(values)}
    grads = {'weights': values}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Check that RMS is bounded for each block
    # Default block size is the full array, so check global RMS
    result = updates['weights']
    rms = jnp.sqrt(jnp.mean(jnp.square(result)))
    
    # RMS should be at most threshold (with small tolerance)
    assert rms <= threshold * 1.01, f"RMS {rms} exceeds threshold {threshold}"


# Test 8: Testing add_decayed_weights
@given(
    params_values=jax_arrays(shape=(3, 3), min_value=-10, max_value=10),
    weight_decay=st.floats(min_value=0, max_value=0.5)
)
@settings(max_examples=100, deadline=5000)
def test_add_decayed_weights(params_values, weight_decay):
    """Test add_decayed_weights adds weight decay correctly."""
    params = {'weights': params_values}
    grads = {'weights': jnp.ones_like(params_values)}
    
    tx = optax.transforms.add_decayed_weights(weight_decay)
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state, params)
    
    # Check the updates include weight decay
    expected = grads['weights'] + weight_decay * params['weights']
    
    np.testing.assert_allclose(updates['weights'], expected, rtol=1e-6)