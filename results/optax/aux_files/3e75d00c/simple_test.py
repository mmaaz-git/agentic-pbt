#!/usr/bin/env python3
"""Simple direct test of optax.contrib properties."""

import jax.numpy as jnp
import optax.contrib
from optax.contrib._complex_valued import _complex_to_real_pair, _real_pair_to_complex

# Test 1: Simple normalize test
print("Test 1: Testing normalize() with simple gradient...")
gradients = {'param': jnp.array([3.0, 4.0])}  # Norm should be 5
normalize_fn = optax.contrib.normalize()
state = normalize_fn.init(gradients)
normalized, _ = normalize_fn.update(gradients, state)
norm = jnp.sqrt(jnp.sum(normalized['param']**2))
print(f"  Original gradient: {gradients['param']}")
print(f"  Normalized gradient: {normalized['param']}")
print(f"  Norm of normalized: {norm}")
print(f"  Expected norm: 1.0")
if abs(float(norm) - 1.0) < 1e-6:
    print("  ✓ Test passed!")
else:
    print(f"  ✗ Test failed! Norm is {norm}, expected 1.0")

# Test 2: Complex to real round-trip
print("\nTest 2: Testing complex to real round-trip...")
complex_array = jnp.array([1+2j, 3+4j, 5+6j])
print(f"  Original: {complex_array}")
real_pair = _complex_to_real_pair(complex_array)
print(f"  Real part: {real_pair.real}")
print(f"  Imaginary part: {real_pair.imaginary}")
recovered = _real_pair_to_complex(real_pair)
print(f"  Recovered: {recovered}")
if jnp.allclose(complex_array, recovered):
    print("  ✓ Test passed!")
else:
    print("  ✗ Test failed! Arrays don't match")

# Test 3: Real array pass-through
print("\nTest 3: Testing real array pass-through...")
real_array = jnp.array([1.0, 2.0, 3.0])
result = _complex_to_real_pair(real_array)
if result is real_array:
    print("  ✓ Real array passed through unchanged")
else:
    print("  ✗ Real array was modified!")

# Test 4: Zero gradient handling
print("\nTest 4: Testing zero gradient handling...")
zero_grads = {'param': jnp.array([0.0, 0.0, 0.0])}
normalize_fn = optax.contrib.normalize()
state = normalize_fn.init(zero_grads)
try:
    normalized, _ = normalize_fn.update(zero_grads, state)
    print(f"  Normalized zero gradient: {normalized['param']}")
    # Check if result is NaN or inf (expected with division by zero)
    if jnp.any(jnp.isnan(normalized['param'])) or jnp.any(jnp.isinf(normalized['param'])):
        print("  ✓ Handled zero gradient (resulted in NaN/inf as expected)")
    else:
        print(f"  ? Unexpected result: {normalized['param']}")
except Exception as e:
    print(f"  ✗ Exception raised: {e}")

# Test 5: reduce_on_plateau validation
print("\nTest 5: Testing reduce_on_plateau parameter validation...")
try:
    # Invalid factor (should raise)
    optax.contrib.reduce_on_plateau(factor=1.5)
    print("  ✗ Should have raised ValueError for factor=1.5")
except ValueError as e:
    print(f"  ✓ Correctly raised ValueError for invalid factor: {e}")

try:
    # Valid parameters (should work)
    opt = optax.contrib.reduce_on_plateau(factor=0.5, rtol=0.01, atol=0.001)
    print("  ✓ Valid parameters accepted")
except Exception as e:
    print(f"  ✗ Unexpected error with valid parameters: {e}")

print("\n" + "="*60)
print("Basic property tests completed!")