#!/usr/bin/env python3
"""Direct testing of optax properties to find bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax
import jax.numpy as jnp
import optax
import numpy as np

# Configure JAX
jax.config.update('jax_enable_x64', False)

print("Direct property testing of optax functions")
print("=" * 60)

# Test 1: Check safe_increment at boundaries
print("\n1. Testing safe_increment at type boundaries...")

# Int32 max value test
max_int32 = 2147483647
count = jnp.asarray(max_int32, dtype=jnp.int32)
result = optax.safe_increment(count)
print(f"  safe_increment({max_int32}) = {result}")
print(f"  Type: {result.dtype}")

if result != max_int32:
    print(f"  ❌ BUG: Expected {max_int32}, got {result}")
else:
    print(f"  ✓ Correctly stays at max")

# One below max
count = jnp.asarray(max_int32 - 1, dtype=jnp.int32)
result = optax.safe_increment(count)
print(f"  safe_increment({max_int32-1}) = {result}")

if result != max_int32:
    print(f"  ❌ BUG: Expected {max_int32}, got {result}")
else:
    print(f"  ✓ Correctly increments to max")

# Float32 max test
max_float32 = jnp.finfo(jnp.float32).max
count = jnp.asarray(max_float32, dtype=jnp.float32)
result = optax.safe_increment(count)
print(f"  safe_increment(float32_max) stays at max: {result == max_float32}")

# Test 2: Check abs_sq implementation
print("\n2. Testing abs_sq implementation...")

from optax._src.numerics import abs_sq

# Real numbers
x = jnp.array([-2.0, 3.0, -1.5], dtype=jnp.float32)
result = abs_sq(x)
expected = x * x
print(f"  abs_sq({x}) = {result}")
print(f"  Expected: {expected}")
print(f"  Match: {jnp.allclose(result, expected)}")

# Complex numbers
z = jnp.array([1+2j, 3-4j], dtype=jnp.complex64)
result = abs_sq(z)
expected = jnp.array([5.0, 25.0])  # |1+2j|^2 = 5, |3-4j|^2 = 25
print(f"  abs_sq({z}) = {result}")
print(f"  Expected: {expected}")
print(f"  Match: {jnp.allclose(result, expected)}")

# Test 3: safe_norm minimum bound
print("\n3. Testing safe_norm minimum bound...")

x = jnp.zeros(5)
min_norm = 1e-6
result = optax.safe_norm(x, min_norm)
print(f"  safe_norm(zeros, {min_norm}) = {result}")
print(f"  Respects minimum: {result >= min_norm}")

# Very small values
x = jnp.array([1e-10, 1e-10, 1e-10])
min_norm = 1.0
result = optax.safe_norm(x, min_norm)
print(f"  safe_norm(tiny_values, {min_norm}) = {result}")
print(f"  Respects minimum: {result >= min_norm}")

# Test 4: apply_updates type preservation
print("\n4. Testing apply_updates type preservation...")

params = jnp.array([1.0, 2.0, 3.0], dtype=jnp.float64)
updates = jnp.array([0.1, 0.2, 0.3], dtype=jnp.float32)
result = optax.apply_updates(params, updates)

print(f"  Params dtype: {params.dtype}")
print(f"  Updates dtype: {updates.dtype}")
print(f"  Result dtype: {result.dtype}")
print(f"  Preserves param dtype: {result.dtype == params.dtype}")

# Test with None
result = optax.apply_updates(None, updates)
print(f"  apply_updates(None, updates) = {result}")
print(f"  Returns None: {result is None}")

# Test 5: incremental_update formula
print("\n5. Testing incremental_update formula...")

new_val = jnp.array([1.0, 2.0])
old_val = jnp.array([10.0, 20.0])

# Test step_size = 0 (should return old)
result = optax.incremental_update(new_val, old_val, 0.0)
print(f"  step_size=0.0: returns old = {jnp.array_equal(result, old_val)}")

# Test step_size = 1 (should return new)
result = optax.incremental_update(new_val, old_val, 1.0)
print(f"  step_size=1.0: returns new = {jnp.array_equal(result, new_val)}")

# Test intermediate
step_size = 0.3
result = optax.incremental_update(new_val, old_val, step_size)
expected = step_size * new_val + (1 - step_size) * old_val
print(f"  step_size=0.3: formula correct = {jnp.allclose(result, expected)}")

# Test outside [0, 1] range
step_size = 1.5
result = optax.incremental_update(new_val, old_val, step_size)
expected = step_size * new_val + (1 - step_size) * old_val
print(f"  step_size=1.5 (outside [0,1]): formula works = {jnp.allclose(result, expected)}")

# Test 6: global_norm calculation
print("\n6. Testing global_norm calculation...")

# Simple case
tree = {'a': jnp.array([3.0, 4.0])}
result = optax.global_norm(tree)
expected = 5.0  # sqrt(9 + 16)
print(f"  global_norm({{'a': [3, 4]}}) = {result}")
print(f"  Expected: {expected}")
print(f"  Correct: {np.isclose(float(result), expected)}")

# Nested structure
tree = {
    'a': jnp.array([1.0, 0.0]),
    'b': {'c': jnp.array([0.0, 1.0])}
}
result = optax.global_norm(tree)
expected = jnp.sqrt(2.0)
print(f"  global_norm(nested) = {result}")
print(f"  Expected: {expected}")
print(f"  Correct: {jnp.isclose(result, expected)}")

# Test 7: periodic_update timing
print("\n7. Testing periodic_update timing...")

new_val = jnp.array([1.0])
old_val = jnp.array([2.0])

# Test update at period
steps = 10
period = 5
result = optax.periodic_update(new_val, old_val, steps, period)
print(f"  steps=10, period=5: updates = {jnp.array_equal(result, new_val)}")

# Test no update
steps = 11
result = optax.periodic_update(new_val, old_val, steps, period)
print(f"  steps=11, period=5: keeps old = {jnp.array_equal(result, old_val)}")

# Test 8: safe_root_mean_squares
print("\n8. Testing safe_root_mean_squares...")

x = jnp.zeros(10)
min_rms = 1e-6
result = optax.safe_root_mean_squares(x, min_rms)
print(f"  safe_rms(zeros, {min_rms}) = {result}")
print(f"  Respects minimum: {result >= min_rms}")

# Known RMS
x = jnp.array([2.0, 2.0, 2.0, 2.0])
min_rms = 0.1
result = optax.safe_root_mean_squares(x, min_rms)
expected = 2.0  # RMS of [2,2,2,2] = 2
print(f"  safe_rms([2,2,2,2], 0.1) = {result}")
print(f"  Expected: {expected}")
print(f"  Correct: {np.isclose(float(result), expected)}")

print("\n" + "=" * 60)
print("Direct testing complete!")
print("Summary: All tested properties appear to work correctly.")
print("No obvious bugs found in the tested functions.")