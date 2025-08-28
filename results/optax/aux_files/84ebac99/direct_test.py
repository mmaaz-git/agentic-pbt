#!/usr/bin/env python3
"""Direct test of optax.losses properties without pytest."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
import optax.losses

print("Testing optax.losses properties...")

# Test 1: l2_loss = 0.5 * squared_error
print("\n1. Testing l2_loss = 0.5 * squared_error")
predictions = jnp.array([1.0, 2.0, 3.0])
targets = jnp.array([1.5, 2.5, 3.5])
l2 = optax.losses.l2_loss(predictions, targets)
squared = optax.losses.squared_error(predictions, targets)
assert jnp.allclose(l2, 0.5 * squared), f"Failed: l2={l2}, 0.5*squared={0.5*squared}"
print("  ✓ Passed")

# Test 2: cosine_distance = 1 - cosine_similarity
print("\n2. Testing cosine_distance = 1 - cosine_similarity")
x = jnp.array([[1.0, 2.0], [3.0, 4.0]])
y = jnp.array([[2.0, 3.0], [4.0, 5.0]])
similarity = optax.losses.cosine_similarity(x, y, epsilon=1e-8)
distance = optax.losses.cosine_distance(x, y, epsilon=1e-8)
assert jnp.allclose(distance, 1.0 - similarity), f"Failed: distance={distance}, 1-similarity={1.0-similarity}"
print("  ✓ Passed")

# Test 3: cosine_similarity(x, x) = 1
print("\n3. Testing cosine_similarity(x, x) = 1")
x = jnp.array([[1.0, 2.0], [3.0, 4.0]])
similarity = optax.losses.cosine_similarity(x, x, epsilon=1e-8)
assert jnp.allclose(similarity, 1.0), f"Failed: similarity={similarity}, expected=1.0"
print("  ✓ Passed")

# Test 4: squared_error(x, x) = 0
print("\n4. Testing squared_error(x, x) = 0")
x = jnp.array([1.0, 2.0, 3.0])
error = optax.losses.squared_error(x, x)
assert jnp.allclose(error, 0.0), f"Failed: error={error}, expected=0"
print("  ✓ Passed")

# Test 5: squared_error with None targets
print("\n5. Testing squared_error(x, None) = squared_error(x, zeros)")
x = jnp.array([1.0, 2.0, 3.0])
error_none = optax.losses.squared_error(x, None)
error_zeros = optax.losses.squared_error(x, jnp.zeros_like(x))
assert jnp.allclose(error_none, error_zeros), f"Failed: error_none={error_none}, error_zeros={error_zeros}"
print("  ✓ Passed")

# Test 6: huber_loss properties
print("\n6. Testing huber_loss properties")
predictions = jnp.array([1.0, 2.0, 5.0])
targets = jnp.array([1.1, 2.0, 2.0])  # errors: 0.1, 0, 3
delta = 1.0
huber = optax.losses.huber_loss(predictions, targets, delta=delta)
# For error=0.1 (< delta): huber = 0.5 * 0.01 = 0.005
# For error=0: huber = 0
# For error=3 (> delta): huber = 0.5 * 1 + 1 * (3-1) = 0.5 + 2 = 2.5
expected = jnp.array([0.005, 0.0, 2.5])
assert jnp.allclose(huber, expected, rtol=1e-5), f"Failed: huber={huber}, expected={expected}"
print("  ✓ Passed")

# Test 7: Test edge case with -inf in weighted_logsoftmax
print("\n7. Testing weighted_logsoftmax with zero weights")
from optax.losses._classification import weighted_logsoftmax
x = jnp.array([1.0, -jnp.inf, 3.0])
weights = jnp.array([1.0, 0.0, 1.0])
result = weighted_logsoftmax(x, weights)
# When weight=0, result should be 0, not NaN
assert result[1] == 0.0, f"Failed: result[1]={result[1]}, expected=0"
assert not jnp.any(jnp.isnan(result)), f"Failed: result contains NaN: {result}"
print("  ✓ Passed")

# Test 8: triplet_margin_loss zero condition
print("\n8. Testing triplet_margin_loss zero condition")
anchors = jnp.array([[1.0, 2.0], [3.0, 4.0]])
positives = anchors + 1e-6  # Very close to anchors
negatives = anchors + 10.0  # Far from anchors
margin = 1.0
loss = optax.losses.triplet_margin_loss(anchors, positives, negatives, margin=margin)
assert jnp.allclose(loss, 0.0, atol=1e-5), f"Failed: loss={loss}, expected≈0"
print("  ✓ Passed")

print("\n" + "="*50)
print("All tests passed! ✅")
print("="*50)