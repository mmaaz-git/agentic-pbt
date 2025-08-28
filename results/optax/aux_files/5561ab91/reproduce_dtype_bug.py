#!/usr/bin/env python3
"""Reproduce the dtype handling bug in optax.perturbations."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax
import jax.numpy as jnp
import optax.perturbations as pert

# Disable JAX's 64-bit mode to see the truncation behavior
jax.config.update("jax_enable_x64", False)

print("=== Testing Normal distribution dtype handling ===")
normal = pert.Normal()
key = jax.random.key(0)

# Request float64
requested_dtype = jnp.float64
samples = normal.sample(key, sample_shape=(3,), dtype=requested_dtype)

print(f"Requested dtype: {requested_dtype}")
print(f"Received dtype:  {samples.dtype}")
print(f"Samples: {samples}")
print(f"Bug: Requested {requested_dtype} but got {samples.dtype}")

print("\n=== Testing Gumbel distribution dtype handling ===")
gumbel = pert.Gumbel()
key2 = jax.random.split(key)[0]

samples_gumbel = gumbel.sample(key2, sample_shape=(3,), dtype=requested_dtype)
print(f"Requested dtype: {requested_dtype}")
print(f"Received dtype:  {samples_gumbel.dtype}") 
print(f"Samples: {samples_gumbel}")
print(f"Bug: Requested {requested_dtype} but got {samples_gumbel.dtype}")

print("\n=== Analysis ===")
print("The bug: When JAX's x64 mode is disabled (which is the default),")
print("the sample() methods silently truncate float64 to float32")
print("but still return float32 arrays instead of respecting the requested dtype.")
print("This violates the API contract where dtype parameter should control output dtype.")

print("\n=== Expected behavior ===")
print("Either:")
print("1. Return arrays with the requested dtype (even if precision is limited)")
print("2. Raise an explicit error when unsupported dtypes are requested")
print("3. Document this limitation clearly in the API")

print("\n=== Checking JAX's underlying behavior ===")
# Check what JAX does directly
direct_normal = jax.random.normal(key, (3,), jnp.float64)
print(f"jax.random.normal with float64: dtype={direct_normal.dtype}")

# The issue is that the distributions pass the dtype directly to JAX functions
# which silently truncate, but the API suggests dtype should be respected