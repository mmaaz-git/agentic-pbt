"""Property-based tests for optax.losses module using Hypothesis."""

import math
import numpy as np
import jax.numpy as jnp
from hypothesis import given, strategies as st, settings, assume
import optax.losses

# Strategies for generating test data
# Use finite floats to avoid NaN/inf issues
safe_floats = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-1e6,
    max_value=1e6
)

# Small arrays for testing
array_1d = st.lists(safe_floats, min_size=1, max_size=10).map(jnp.array)
array_2d = st.lists(
    st.lists(safe_floats, min_size=2, max_size=5),
    min_size=2, max_size=5
).map(lambda x: jnp.array(x))

# Positive floats for certain parameters
positive_floats = st.floats(min_value=1e-6, max_value=1e6)


# Test 1: l2_loss = 0.5 * squared_error (explicitly documented relationship)
@given(array_1d, array_1d)
@settings(max_examples=100)
def test_l2_loss_is_half_squared_error(predictions, targets):
    """Test that l2_loss(x, y) = 0.5 * squared_error(x, y)."""
    # Ensure same shape
    min_len = min(len(predictions), len(targets))
    predictions = predictions[:min_len]
    targets = targets[:min_len]
    
    l2 = optax.losses.l2_loss(predictions, targets)
    squared = optax.losses.squared_error(predictions, targets)
    
    # This relationship is explicitly documented in the code
    assert jnp.allclose(l2, 0.5 * squared, rtol=1e-5)


# Test 2: cosine_distance = 1 - cosine_similarity (documented relationship)
@given(array_2d, array_2d)
@settings(max_examples=100)
def test_cosine_distance_similarity_relationship(predictions, targets):
    """Test that cosine_distance = 1 - cosine_similarity."""
    # Ensure same shape
    min_shape = (
        min(predictions.shape[0], targets.shape[0]),
        min(predictions.shape[1], targets.shape[1])
    )
    predictions = predictions[:min_shape[0], :min_shape[1]]
    targets = targets[:min_shape[0], :min_shape[1]]
    
    # Avoid zero vectors which would make cosine similarity undefined
    assume(jnp.linalg.norm(predictions) > 1e-6)
    assume(jnp.linalg.norm(targets) > 1e-6)
    
    similarity = optax.losses.cosine_similarity(predictions, targets, epsilon=1e-8)
    distance = optax.losses.cosine_distance(predictions, targets, epsilon=1e-8)
    
    # The code explicitly implements: distance = 1.0 - similarity
    assert jnp.allclose(distance, 1.0 - similarity, rtol=1e-5)


# Test 3: cosine_similarity(x, x) = 1 for non-zero vectors
@given(array_2d)
@settings(max_examples=100)
def test_cosine_self_similarity(x):
    """Test that cosine_similarity(x, x) = 1 for non-zero x."""
    # Ensure non-zero vector
    assume(jnp.linalg.norm(x) > 1e-6)
    
    similarity = optax.losses.cosine_similarity(x, x, epsilon=1e-8)
    
    # Self-similarity should be 1.0 for normalized vectors
    assert jnp.allclose(similarity, 1.0, rtol=1e-5)


# Test 4: squared_error(x, x) = 0 (identity property)
@given(array_1d)
@settings(max_examples=100)
def test_squared_error_identity(x):
    """Test that squared_error(x, x) = 0."""
    error = optax.losses.squared_error(x, x)
    
    # Error between identical arrays should be zero
    assert jnp.allclose(error, 0.0, atol=1e-7)


# Test 5: squared_error with None targets treats them as zeros
@given(array_1d)
@settings(max_examples=100)
def test_squared_error_none_targets(predictions):
    """Test that squared_error(x, None) = squared_error(x, zeros)."""
    error_none = optax.losses.squared_error(predictions, None)
    error_zeros = optax.losses.squared_error(predictions, jnp.zeros_like(predictions))
    
    # The documentation states None is treated as zeros
    assert jnp.allclose(error_none, error_zeros, rtol=1e-7)


# Test 6: huber_loss properties
@given(array_1d, array_1d, positive_floats)
@settings(max_examples=100)
def test_huber_loss_properties(predictions, targets, delta):
    """Test huber_loss behaves correctly for small and large errors."""
    # Ensure same shape
    min_len = min(len(predictions), len(targets))
    predictions = predictions[:min_len]
    targets = targets[:min_len]
    
    huber = optax.losses.huber_loss(predictions, targets, delta=delta)
    
    # Huber loss should always be non-negative
    assert jnp.all(huber >= -1e-7)
    
    # For small errors (|error| <= delta), huber ≈ 0.5 * error^2
    errors = predictions - targets
    small_mask = jnp.abs(errors) <= delta
    if jnp.any(small_mask):
        expected_small = 0.5 * errors[small_mask]**2
        assert jnp.allclose(huber[small_mask], expected_small, rtol=1e-5)


# Test 7: hinge_loss is non-negative
@given(array_1d, st.lists(st.sampled_from([-1, 1]), min_size=1, max_size=10).map(jnp.array))
@settings(max_examples=100)
def test_hinge_loss_non_negative(predictions, targets):
    """Test that hinge_loss is always non-negative."""
    # Ensure same shape
    min_len = min(len(predictions), len(targets))
    predictions = predictions[:min_len]
    targets = targets[:min_len]
    
    loss = optax.losses.hinge_loss(predictions, targets)
    
    # Hinge loss is max(0, 1 - y*f(x)), so always >= 0
    assert jnp.all(loss >= -1e-7)


# Test 8: log_cosh approximations
@given(array_1d, array_1d)
@settings(max_examples=100)
def test_log_cosh_properties(predictions, targets):
    """Test log_cosh loss approximation properties."""
    # Ensure same shape
    min_len = min(len(predictions), len(targets))
    predictions = predictions[:min_len]
    targets = targets[:min_len]
    
    loss = optax.losses.log_cosh(predictions, targets)
    errors = predictions - targets
    
    # For small errors, log(cosh(x)) ≈ x^2/2
    small_errors_mask = jnp.abs(errors) < 0.1
    if jnp.any(small_errors_mask):
        expected_small = errors[small_errors_mask]**2 / 2
        actual_small = loss[small_errors_mask]
        # Relaxed tolerance for approximation
        assert jnp.allclose(actual_small, expected_small, rtol=0.1, atol=0.01)


# Test 9: triplet_margin_loss = 0 when condition is met
@given(array_2d, array_2d, array_2d, positive_floats)
@settings(max_examples=100)
def test_triplet_margin_loss_zero_condition(anchors, positives, negatives, margin):
    """Test triplet_margin_loss = 0 when pos_dist + margin < neg_dist."""
    # Ensure all have same shape
    min_shape = (
        min(anchors.shape[0], positives.shape[0], negatives.shape[0]),
        min(anchors.shape[1], positives.shape[1], negatives.shape[1])
    )
    anchors = anchors[:min_shape[0], :min_shape[1]]
    positives = positives[:min_shape[0], :min_shape[1]]
    negatives = negatives[:min_shape[0], :min_shape[1]]
    
    # Make positives very close to anchors and negatives far
    # This ensures pos_dist + margin < neg_dist
    positives = anchors + jnp.ones_like(anchors) * 1e-6
    negatives = anchors + jnp.ones_like(anchors) * (margin + 10)
    
    loss = optax.losses.triplet_margin_loss(
        anchors, positives, negatives, margin=margin
    )
    
    # When positive distance + margin < negative distance, loss should be 0
    assert jnp.allclose(loss, 0.0, atol=1e-5)


# Test 10: Test the weighted_logsoftmax convention for 0*log(0) = 0
@given(
    st.lists(safe_floats, min_size=2, max_size=10).map(jnp.array),
    st.lists(st.floats(min_value=0, max_value=1), min_size=2, max_size=10).map(jnp.array)
)
@settings(max_examples=100)
def test_weighted_logsoftmax_zero_weight_convention(x, weights):
    """Test that weighted_logsoftmax returns 0 when weights=0."""
    # Ensure same length
    min_len = min(len(x), len(weights))
    x = x[:min_len]
    weights = weights[:min_len]
    
    # Set some weights to exactly 0
    zero_indices = jnp.array([0, min_len-1] if min_len > 1 else [0])
    weights = weights.at[zero_indices].set(0.0)
    
    # Import the internal function (it's not exposed in __init__.py)
    from optax.losses._classification import weighted_logsoftmax
    
    result = weighted_logsoftmax(x, weights)
    
    # Where weights are 0, result should be 0 (not NaN), as documented
    assert jnp.all(jnp.where(weights == 0, result == 0, True))
    assert not jnp.any(jnp.isnan(result))


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])