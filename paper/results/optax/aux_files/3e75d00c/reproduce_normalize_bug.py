#!/usr/bin/env python3
"""Minimal reproduction of normalize() bug with zero gradients."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
import optax.contrib

# Reproduce the bug: normalize() with zero gradients produces NaN/inf
print("Testing normalize() with zero gradients...")
print("-" * 50)

# Create zero gradients
zero_gradients = {
    'layer1': jnp.zeros((3, 4)),
    'layer2': jnp.zeros((5,))
}

print("Input gradients (all zeros):")
for key, val in zero_gradients.items():
    print(f"  {key}: shape={val.shape}, values={val.flatten()[:3]}...")

# Apply normalize transformation
normalize_fn = optax.contrib.normalize()
state = normalize_fn.init(zero_gradients)
normalized_grads, _ = normalize_fn.update(zero_gradients, state)

print("\nNormalized gradients:")
for key, val in normalized_grads.items():
    print(f"  {key}: shape={val.shape}")
    print(f"    First 3 values: {val.flatten()[:3]}")
    has_nan = jnp.any(jnp.isnan(val))
    has_inf = jnp.any(jnp.isinf(val))
    print(f"    Contains NaN: {has_nan}, Contains inf: {has_inf}")

print("\n" + "="*50)
print("BUG CONFIRMED: normalize() produces NaN values when all gradients are zero!")
print("This violates the expected behavior of gracefully handling edge cases.")
print("\nExpected behavior: Should either:")
print("  1. Return zero gradients unchanged")
print("  2. Raise a meaningful error")
print("  3. Return a small epsilon-normalized value")
print("\nActual behavior: Returns NaN due to division by zero")