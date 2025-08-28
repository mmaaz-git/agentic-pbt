import math
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, assume, settings, example
import pytest


# Helper strategies
@st.composite
def jax_arrays_edge(draw, shape=None):
    """Generate JAX arrays with edge case values."""
    if shape is None:
        shape = draw(st.tuples(st.integers(1, 5), st.integers(1, 5)))
    
    # Include edge cases: very small, very large, zero
    elements = st.one_of(
        st.floats(min_value=-1e-30, max_value=1e-30),  # Very small
        st.floats(min_value=1e20, max_value=1e30),     # Very large
        st.just(0.0),                                   # Zero
        st.floats(min_value=-1e10, max_value=1e10),    # Normal range
    )
    
    array = draw(st.lists(elements, min_size=int(np.prod(shape)), max_size=int(np.prod(shape))))
    return jnp.array(array).reshape(shape)


# Test 1: clip with extreme values
@given(
    extreme_value=st.one_of(
        st.floats(min_value=1e20, max_value=1e30),
        st.floats(min_value=-1e30, max_value=-1e20)
    ),
    max_delta=st.floats(min_value=1e-10, max_value=1e10)
)
@settings(max_examples=200, deadline=5000)
def test_clip_extreme_values(extreme_value, max_delta):
    """Test clip with extreme gradient values."""
    tx = optax.transforms.clip(max_delta)
    
    params = {'x': jnp.array([0.0])}
    grads = {'x': jnp.array([extreme_value])}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Check clipping works even with extreme values
    result = updates['x'][0]
    assert abs(result) <= max_delta * 1.01, f"Extreme value {extreme_value} not clipped to {max_delta}"
    
    # Check sign is preserved
    if extreme_value != 0:
        assert jnp.sign(result) == jnp.sign(extreme_value), "Sign not preserved after clipping"


# Test 2: chain of many transformations
@given(
    values=jax_arrays_edge(shape=(3, 3)),
    num_clips=st.integers(min_value=2, max_value=10)
)
@settings(max_examples=100, deadline=5000)
def test_chain_many_transforms(values, num_clips):
    """Test chaining many clip transformations."""
    # Create a chain of progressively smaller clips
    transforms = []
    for i in range(num_clips):
        max_delta = 10.0 / (i + 1)
        transforms.append(optax.transforms.clip(max_delta))
    
    tx = optax.chain(*transforms)
    
    params = {'weights': jnp.zeros_like(values)}
    grads = {'weights': values}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Final clipping should be the smallest (10.0 / num_clips)
    final_max = 10.0 / num_clips
    assert jnp.all(jnp.abs(updates['weights']) <= final_max * 1.01)


# Test 3: zero_nans with inf values
@given(shape=st.tuples(st.integers(2, 5), st.integers(2, 5)))
@settings(max_examples=100, deadline=5000)
def test_zero_nans_preserves_inf(shape):
    """Test that zero_nans preserves infinity values."""
    tx = optax.transforms.zero_nans()
    
    # Create array with mix of inf, -inf, nan, and normal values
    arr = np.random.randn(*shape)
    arr[0, 0] = np.inf
    arr[0, 1] = -np.inf
    arr[1, 0] = np.nan
    
    params = {'x': jnp.zeros(shape)}
    grads = {'x': jnp.array(arr)}
    
    state = tx.init(params)
    updates, new_state = tx.update(grads, state)
    
    result = updates['x']
    
    # Check inf values are preserved
    assert result[0, 0] == np.inf, "Positive infinity not preserved"
    assert result[0, 1] == -np.inf, "Negative infinity not preserved"
    
    # Check NaN is replaced with 0
    assert result[1, 0] == 0, "NaN not replaced with 0"
    
    # The state is a ZeroNansState object, check its found_nan field
    assert hasattr(new_state, 'found_nan'), "State doesn't have found_nan field"
    # found_nan is a scalar boolean indicating if any NaN was found in the array
    assert new_state.found_nan['x'] == True, "State didn't record NaN was found"


# Test 4: keep_params_nonnegative with negative params
@given(
    negative_params=st.floats(min_value=-100, max_value=-0.1),
    update_value=st.floats(min_value=-10, max_value=10)
)
@settings(max_examples=100, deadline=5000)
def test_keep_params_nonnegative_negative_params(negative_params, update_value):
    """Test keep_params_nonnegative with initially negative params."""
    tx = optax.transforms.keep_params_nonnegative()
    
    # Start with negative params (violates precondition)
    params = {'x': jnp.array([negative_params])}
    grads = {'x': jnp.array([update_value])}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state, params)
    
    # Should move params to 0 regardless of update
    new_params = params['x'] + updates['x']
    assert new_params[0] >= -1e-7, f"Negative params {negative_params} not corrected to non-negative"


# Test 5: EMA with zero decay
@given(value=st.floats(min_value=-100, max_value=100, allow_nan=False))
@settings(max_examples=100, deadline=5000)
def test_ema_zero_decay(value):
    """Test EMA with decay=0 should return the gradient unchanged."""
    tx = optax.transforms.ema(decay=0.0, debias=False)
    
    params = {'x': jnp.zeros(3)}
    grads = {'x': jnp.array([value, value, value])}
    
    state = tx.init(params)
    
    # First update with decay=0 should return gradient unchanged
    updates, state = tx.update(grads, state)
    
    # Note: very small values may underflow to zero in float32
    # This is expected behavior for values below ~1e-45
    if abs(value) < 1e-38:  # Below float32 normal range
        # Value might be zero due to underflow
        if jnp.all(updates['x'] == 0):
            return  # This is acceptable for tiny values
    
    np.testing.assert_allclose(updates['x'], grads['x'], rtol=1e-7)


# Test 6: clip_by_global_norm with zero norm
@given(shape=st.tuples(st.integers(1, 5), st.integers(1, 5)))
@settings(max_examples=100, deadline=5000)
def test_clip_by_global_norm_zero_grads(shape):
    """Test clip_by_global_norm with zero gradients."""
    tx = optax.transforms.clip_by_global_norm(1.0)
    
    params = {'x': jnp.ones(shape)}
    grads = {'x': jnp.zeros(shape)}  # Zero gradients
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Zero gradients should remain zero
    assert jnp.all(updates['x'] == 0), "Zero gradients modified by clip_by_global_norm"


# Test 7: Testing with empty pytrees
@given(max_norm=st.floats(min_value=0.1, max_value=10))
@settings(max_examples=100, deadline=5000)
def test_transforms_empty_pytree(max_norm):
    """Test transforms handle empty pytrees correctly."""
    tx = optax.transforms.clip_by_global_norm(max_norm)
    
    params = {}  # Empty pytree
    grads = {}   # Empty pytree
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    assert updates == {}, "Empty pytree not preserved"


# Test 8: apply_if_finite with nan/inf
@given(
    has_nan=st.booleans(),
    has_inf=st.booleans()
)
@settings(max_examples=100, deadline=5000)
def test_apply_if_finite(has_nan, has_inf):
    """Test apply_if_finite skips updates with nan/inf."""
    # Inner transform that doubles values
    inner_tx = optax.transforms.trace(decay=0.0)  # Acts like identity with decay=0
    tx = optax.transforms.apply_if_finite(inner_tx, max_consecutive_errors=3)
    
    # Create gradients with optional nan/inf
    grad_values = [1.0, 2.0, 3.0]
    if has_nan:
        grad_values[0] = np.nan
    if has_inf:
        grad_values[1] = np.inf
    
    params = {'x': jnp.array([0.0, 0.0, 0.0])}
    grads = {'x': jnp.array(grad_values)}
    
    state = tx.init(params)
    updates, new_state = tx.update(grads, state)
    
    if has_nan or has_inf:
        # Should return zeros when nan/inf present
        assert jnp.all(updates['x'] == 0), "Non-finite values not handled correctly"
        # Should increment error count
        assert new_state.notfinite_count > 0
    else:
        # Should apply inner transform normally
        np.testing.assert_allclose(updates['x'], grads['x'], rtol=1e-7)


# Test 9: Complex interaction - clip after add_decayed_weights
@given(
    params_val=st.floats(min_value=10, max_value=100),
    weight_decay=st.floats(min_value=0.1, max_value=1.0),
    max_delta=st.floats(min_value=0.1, max_value=5.0)
)
@settings(max_examples=100, deadline=5000)
def test_clip_after_weight_decay(params_val, weight_decay, max_delta):
    """Test interaction between weight decay and clipping."""
    # Chain: first add weight decay, then clip
    tx = optax.chain(
        optax.transforms.add_decayed_weights(weight_decay),
        optax.transforms.clip(max_delta)
    )
    
    params = {'x': jnp.array([params_val])}
    grads = {'x': jnp.array([0.0])}  # Zero gradient
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state, params)
    
    # Weight decay adds params * weight_decay to gradient
    # This should then be clipped
    expected = weight_decay * params_val
    if expected > max_delta:
        expected = max_delta
    elif expected < -max_delta:
        expected = -max_delta
    
    np.testing.assert_allclose(updates['x'][0], expected, rtol=1e-6)


# Test 10: Test numerical stability with very small values
@given(
    tiny_value=st.floats(min_value=1e-30, max_value=1e-20),
    max_norm=st.floats(min_value=1e-10, max_value=1.0)
)
@settings(max_examples=100, deadline=5000)
def test_clip_by_global_norm_tiny_values(tiny_value, max_norm):
    """Test clip_by_global_norm with very small gradient values."""
    tx = optax.transforms.clip_by_global_norm(max_norm)
    
    params = {'x': jnp.array([0.0, 0.0])}
    grads = {'x': jnp.array([tiny_value, tiny_value])}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Should preserve the gradient structure even with tiny values
    # Global norm should still be at most max_norm
    global_norm = jnp.sqrt(jnp.sum(jnp.square(updates['x'])))
    assert global_norm <= max_norm * 1.01 or global_norm < 1e-20