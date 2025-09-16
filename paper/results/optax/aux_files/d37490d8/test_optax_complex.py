import math
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, assume, settings, example
import pytest


# Helper to generate pytrees
@st.composite 
def simple_pytree(draw):
    """Generate simple pytree with consistent structure."""
    shape = draw(st.tuples(st.integers(2, 5), st.integers(2, 5)))
    values = draw(st.floats(min_value=-10, max_value=10))
    
    return {
        'layer1': jnp.full(shape, values),
        'layer2': jnp.full(shape, values * 2)
    }


# Test 1: MultiSteps accumulates correctly
@given(
    params=simple_pytree(),
    every_k_schedule=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=100, deadline=5000)
def test_multi_steps_accumulation(params, every_k_schedule):
    """Test that MultiSteps accumulates gradients correctly over k steps."""
    tx = optax.MultiSteps(optax.identity(), every_k_schedule)
    
    # Constant gradients for easy verification
    grads = jax.tree.map(lambda x: jnp.ones_like(x), params)
    
    state = tx.init(params)
    
    # Accumulate for k-1 steps
    for step in range(every_k_schedule - 1):
        updates, state = tx.update(grads, state)
        # Should return zeros until k-th step
        assert all(jnp.all(u == 0) for u in jax.tree.leaves(updates)), \
            f"Non-zero updates at step {step+1}, expected zeros"
    
    # k-th step should return accumulated gradients
    updates, state = tx.update(grads, state)
    
    # Should return k * grads (since we accumulated k times)
    expected = jax.tree.map(lambda g: g * every_k_schedule, grads)
    
    def assert_close(actual, expected):
        np.testing.assert_allclose(actual, expected, rtol=1e-6)
    
    jax.tree.map(assert_close, updates, expected)


# Test 2: trace vs ema difference
@given(
    value=st.floats(min_value=-10, max_value=10, allow_nan=False),
    decay=st.floats(min_value=0.5, max_value=0.95)
)
@settings(max_examples=100, deadline=5000)
def test_trace_vs_ema_difference(value, decay):
    """Test that trace and ema produce different results as documented."""
    # trace: t = decay * trace + updates
    # ema: t = decay * ema + (1-decay) * updates
    tx_trace = optax.transforms.trace(decay=decay, nesterov=False)
    tx_ema = optax.transforms.ema(decay=decay, debias=False)
    
    params = {'x': jnp.zeros(3)}
    grads = {'x': jnp.array([value, value, value])}
    
    # Initialize both
    state_trace = tx_trace.init(params)
    state_ema = tx_ema.init(params)
    
    # Apply updates
    updates_trace, _ = tx_trace.update(grads, state_trace)
    updates_ema, _ = tx_ema.update(grads, state_ema)
    
    # They should produce different results (unless value is 0)
    if value != 0:
        # trace returns: updates (first iteration with zero init)
        # ema returns: (1-decay) * updates (first iteration with zero init)
        expected_trace = grads['x']
        expected_ema = (1 - decay) * grads['x']
        
        np.testing.assert_allclose(updates_trace['x'], expected_trace, rtol=1e-6)
        np.testing.assert_allclose(updates_ema['x'], expected_ema, rtol=1e-6)


# Test 3: conditionally_mask behavior
@given(
    params=simple_pytree(),
    mask_layer1=st.booleans(),
    mask_layer2=st.booleans()
)
@settings(max_examples=100, deadline=5000)
def test_conditionally_mask(params, mask_layer1, mask_layer2):
    """Test conditionally_mask correctly applies masking."""
    
    # Create condition function that masks based on step
    def should_update(step, grad):
        # Update layer1 if mask_layer1, layer2 if mask_layer2
        return {'layer1': mask_layer1, 'layer2': mask_layer2}
    
    tx = optax.transforms.conditionally_mask(should_update)
    
    grads = jax.tree.map(lambda x: jnp.ones_like(x), params)
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # Check masking is applied correctly
    if mask_layer1:
        np.testing.assert_allclose(updates['layer1'], grads['layer1'])
    else:
        assert jnp.all(updates['layer1'] == 0), "layer1 should be masked (zeros)"
    
    if mask_layer2:
        np.testing.assert_allclose(updates['layer2'], grads['layer2'])
    else:
        assert jnp.all(updates['layer2'] == 0), "layer2 should be masked (zeros)"


# Test 4: freeze function
@given(
    params=simple_pytree(),
    freeze_layer1=st.booleans()
)
@settings(max_examples=100, deadline=5000)
def test_freeze_transform(params, freeze_layer1):
    """Test freeze correctly prevents updates to specified parameters."""
    
    # Create mask to freeze layer1 if requested
    mask = {
        'layer1': not freeze_layer1,  # True means update, False means freeze
        'layer2': True
    }
    
    tx = optax.transforms.freeze(mask)
    
    grads = jax.tree.map(lambda x: jnp.ones_like(x) * 5, params)
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    if freeze_layer1:
        # layer1 should have zero updates (frozen)
        assert jnp.all(updates['layer1'] == 0), "Frozen layer1 has non-zero updates"
    else:
        # layer1 should have normal updates
        np.testing.assert_allclose(updates['layer1'], grads['layer1'])
    
    # layer2 should always have normal updates
    np.testing.assert_allclose(updates['layer2'], grads['layer2'])


# Test 5: skip_large_updates
@given(
    normal_grad=st.floats(min_value=-1, max_value=1),
    large_grad=st.floats(min_value=100, max_value=1000),
    max_norm=st.floats(min_value=5, max_value=10)
)
@settings(max_examples=100, deadline=5000)
def test_skip_large_updates(normal_grad, large_grad, max_norm):
    """Test skip_large_updates correctly skips updates above threshold."""
    tx = optax.transforms.skip_large_updates(max_norm=max_norm)
    
    params = {'normal': jnp.array([0.0]), 'large': jnp.array([0.0])}
    
    # Create grads with one normal and one large update
    grads = {
        'normal': jnp.array([normal_grad]),
        'large': jnp.array([large_grad])
    }
    
    state = tx.init(params)
    updates, new_state = tx.update(grads, state, params)
    
    # Calculate global norm
    global_norm = jnp.sqrt(normal_grad**2 + large_grad**2)
    
    if global_norm > max_norm:
        # Should skip - all updates should be zero
        assert jnp.all(updates['normal'] == 0), "Updates not skipped despite large norm"
        assert jnp.all(updates['large'] == 0), "Updates not skipped despite large norm"
        assert new_state.should_skip == True, "State doesn't indicate skip"
    else:
        # Should not skip - updates should be unchanged
        np.testing.assert_allclose(updates['normal'], grads['normal'])
        np.testing.assert_allclose(updates['large'], grads['large'])
        assert new_state.should_skip == False, "State incorrectly indicates skip"


# Test 6: adaptive_grad_clip edge case
@given(
    grad_val=st.floats(min_value=-100, max_value=100),
    clipping_val=st.floats(min_value=0.01, max_value=1.0),
    eps=st.floats(min_value=1e-8, max_value=1e-3)
)
@settings(max_examples=100, deadline=5000)
def test_adaptive_grad_clip(grad_val, clipping_val, eps):
    """Test adaptive gradient clipping."""
    tx = optax.transforms.adaptive_grad_clip(clipping=clipping_val, eps=eps)
    
    params = {'x': jnp.array([1.0, 2.0, 3.0])}
    grads = {'x': jnp.array([grad_val, grad_val/2, grad_val/3])}
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state, params)
    
    # Adaptive clipping formula: g_norm / max(1, g_norm / (c * p_norm))
    g_norm = jnp.linalg.norm(grads['x'])
    p_norm = jnp.linalg.norm(params['x'])
    
    # Updates should be bounded but proportional
    u_norm = jnp.linalg.norm(updates['x'])
    
    # Check the clipping constraint
    max_allowed = clipping_val * p_norm + eps
    assert u_norm <= max_allowed * 1.01, f"Update norm {u_norm} exceeds allowed {max_allowed}"


# Test 7: Test partition transform
@given(
    layer1_vals=st.floats(min_value=-10, max_value=10),
    layer2_vals=st.floats(min_value=-10, max_value=10),
    clip_val=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100, deadline=5000)
def test_partition_transform(layer1_vals, layer2_vals, clip_val):
    """Test partition applies different transforms to different parts."""
    
    # Apply clipping only to layer1
    def partition_fn(path, _):
        return 0 if 'layer1' in path else 1
    
    # Two optimizers: clip for partition 0, identity for partition 1
    optimizers = {
        0: optax.transforms.clip(clip_val),
        1: optax.identity()
    }
    
    tx = optax.transforms.partition(optimizers, partition_fn)
    
    params = {
        'layer1': jnp.array([0.0, 0.0]),
        'layer2': jnp.array([0.0, 0.0])
    }
    
    grads = {
        'layer1': jnp.array([layer1_vals, layer1_vals * 2]),
        'layer2': jnp.array([layer2_vals, layer2_vals * 2])
    }
    
    state = tx.init(params)
    updates, _ = tx.update(grads, state)
    
    # layer1 should be clipped
    assert jnp.all(jnp.abs(updates['layer1']) <= clip_val * 1.01), \
        f"layer1 not clipped: {updates['layer1']}"
    
    # layer2 should be unchanged
    np.testing.assert_allclose(updates['layer2'], grads['layer2'], rtol=1e-6)