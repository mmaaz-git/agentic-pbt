#!/usr/bin/env python3
"""Minimal property-based tests for optax to find bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import math
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, settings
from hypothesis.extra import numpy as hnp

# Configure JAX
jax.config.update('jax_enable_x64', False)  # Use float32 for consistency

print("Testing optax properties...")

# Test 1: safe_increment at integer boundaries
print("\n1. Testing safe_increment at boundaries...")
try:
    # Test with int32 max value
    max_int32 = 2147483647
    count = jnp.asarray(max_int32, dtype=jnp.int32)
    result = optax.safe_increment(count)
    
    if result != max_int32:
        print(f"  ❌ BUG FOUND: safe_increment({max_int32}) returned {result}, expected {max_int32}")
    else:
        print(f"  ✓ safe_increment at int32 max works correctly")
    
    # Test one below max
    count = jnp.asarray(max_int32 - 1, dtype=jnp.int32)
    result = optax.safe_increment(count)
    if result != max_int32:
        print(f"  ❌ BUG FOUND: safe_increment({max_int32-1}) returned {result}, expected {max_int32}")
    else:
        print(f"  ✓ safe_increment one below max works correctly")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 2: abs_sq with edge cases
print("\n2. Testing abs_sq with various inputs...")
try:
    from optax._src.numerics import abs_sq
    
    # Test with zeros
    x = jnp.zeros(5)
    result = abs_sq(x)
    if not jnp.allclose(result, 0):
        print(f"  ❌ BUG: abs_sq(zeros) = {result}, expected zeros")
    else:
        print(f"  ✓ abs_sq(zeros) works")
    
    # Test with negative values
    x = jnp.array([-2.0, -3.0, -1.0])
    result = abs_sq(x)
    expected = jnp.array([4.0, 9.0, 1.0])
    if not jnp.allclose(result, expected):
        print(f"  ❌ BUG: abs_sq({x}) = {result}, expected {expected}")
    else:
        print(f"  ✓ abs_sq with negative values works")
    
    # Test with complex numbers
    z = jnp.array([1+2j, 3-4j])
    result = abs_sq(z)
    expected = jnp.array([5.0, 25.0])  # |1+2j|^2 = 1^2 + 2^2 = 5, |3-4j|^2 = 9+16 = 25
    if not jnp.allclose(result, expected):
        print(f"  ❌ BUG: abs_sq({z}) = {result}, expected {expected}")
    else:
        print(f"  ✓ abs_sq with complex numbers works")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 3: safe_norm edge cases
print("\n3. Testing safe_norm invariant...")
try:
    # Test with zero vector and min_norm
    x = jnp.zeros(5)
    min_norm = 1e-6
    result = optax.safe_norm(x, min_norm)
    
    if result < min_norm:
        print(f"  ❌ BUG: safe_norm(zeros, {min_norm}) = {result} < min_norm")
    else:
        print(f"  ✓ safe_norm with zero vector respects min_norm")
    
    # Test with very small values
    x = jnp.array([1e-10, 1e-10, 1e-10])
    min_norm = 1.0
    result = optax.safe_norm(x, min_norm)
    
    if result < min_norm:
        print(f"  ❌ BUG: safe_norm(small_values, {min_norm}) = {result} < min_norm")
    else:
        print(f"  ✓ safe_norm with small values respects min_norm")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 4: apply_updates with None
print("\n4. Testing apply_updates with None handling...")
try:
    # Test None params
    result = optax.apply_updates(None, jnp.array([1.0, 2.0]))
    if result is not None:
        print(f"  ❌ BUG: apply_updates(None, updates) returned {result}, expected None")
    else:
        print(f"  ✓ apply_updates handles None params correctly")
    
    # Test tree with None
    params = {'a': jnp.array([1.0]), 'b': None}
    updates = {'a': jnp.array([0.1]), 'b': jnp.array([0.2])}
    result = optax.apply_updates(params, updates)
    
    if result['b'] is not None:
        print(f"  ❌ BUG: apply_updates didn't preserve None in tree")
    else:
        print(f"  ✓ apply_updates preserves None in trees")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 5: incremental_update edge cases
print("\n5. Testing incremental_update polyak averaging...")
try:
    # Test with step_size = 0 (should return old)
    new_val = jnp.array([1.0, 2.0, 3.0])
    old_val = jnp.array([10.0, 20.0, 30.0])
    result = optax.incremental_update(new_val, old_val, 0.0)
    
    if not jnp.allclose(result, old_val):
        print(f"  ❌ BUG: incremental_update with step_size=0 didn't return old values")
    else:
        print(f"  ✓ incremental_update with step_size=0 works")
    
    # Test with step_size = 1 (should return new)
    result = optax.incremental_update(new_val, old_val, 1.0)
    if not jnp.allclose(result, new_val):
        print(f"  ❌ BUG: incremental_update with step_size=1 didn't return new values")
    else:
        print(f"  ✓ incremental_update with step_size=1 works")
    
    # Test intermediate value
    result = optax.incremental_update(new_val, old_val, 0.3)
    expected = 0.3 * new_val + 0.7 * old_val
    if not jnp.allclose(result, expected):
        print(f"  ❌ BUG: incremental_update formula incorrect")
        print(f"    Got: {result}")
        print(f"    Expected: {expected}")
    else:
        print(f"  ✓ incremental_update formula works correctly")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 6: global_norm 
print("\n6. Testing global_norm...")
try:
    # Simple test
    tree = {'a': jnp.array([3.0, 4.0])}  # norm should be 5
    result = optax.global_norm(tree)
    expected = 5.0
    
    if not math.isclose(float(result), expected, rel_tol=1e-6):
        print(f"  ❌ BUG: global_norm({tree}) = {result}, expected {expected}")
    else:
        print(f"  ✓ global_norm simple case works")
    
    # Test with nested structure
    tree = {
        'a': jnp.array([1.0, 0.0]),
        'b': {'c': jnp.array([0.0, 1.0, 0.0])}
    }
    result = optax.global_norm(tree)
    expected = jnp.sqrt(2.0)  # sqrt(1^2 + 1^2)
    
    if not math.isclose(float(result), float(expected), rel_tol=1e-6):
        print(f"  ❌ BUG: global_norm nested structure incorrect")
    else:
        print(f"  ✓ global_norm with nested structure works")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 7: More comprehensive safe_increment test
print("\n7. Testing safe_increment with float32...")
try:
    # Test with float32 near max
    max_float32 = jnp.finfo(jnp.float32).max
    
    # Test at max
    count = jnp.asarray(max_float32, dtype=jnp.float32)
    result = optax.safe_increment(count)
    
    if result != max_float32:
        print(f"  ❌ BUG: safe_increment at float32 max changed the value")
        print(f"    Input: {count}")
        print(f"    Output: {result}")
    else:
        print(f"  ✓ safe_increment at float32 max stays at max")
    
    # Test just below max
    count = jnp.asarray(max_float32 - 1e30, dtype=jnp.float32)
    result = optax.safe_increment(count) 
    
    # The result should either be max or count+1, but definitely not overflow
    if jnp.isinf(result) or jnp.isnan(result):
        print(f"  ❌ BUG: safe_increment caused overflow/NaN")
        print(f"    Input: {count}")
        print(f"    Output: {result}")
    else:
        print(f"  ✓ safe_increment near float32 max doesn't overflow")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 8: safe_root_mean_squares
print("\n8. Testing safe_root_mean_squares...")
try:
    # Test with zero array
    x = jnp.zeros(10)
    min_rms = 1e-6
    result = optax.safe_root_mean_squares(x, min_rms)
    
    if result < min_rms:
        print(f"  ❌ BUG: safe_root_mean_squares(zeros) = {result} < {min_rms}")
    else:
        print(f"  ✓ safe_root_mean_squares with zeros respects min_rms")
    
    # Test actual RMS calculation
    x = jnp.array([2.0, 2.0, 2.0, 2.0])  # RMS should be 2.0
    min_rms = 0.1
    result = optax.safe_root_mean_squares(x, min_rms)
    
    if not math.isclose(float(result), 2.0, rel_tol=1e-6):
        print(f"  ❌ BUG: safe_root_mean_squares calculation incorrect")
        print(f"    Input: {x}, min_rms: {min_rms}")
        print(f"    Got: {result}, expected: 2.0")
    else:
        print(f"  ✓ safe_root_mean_squares calculation correct")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")

print("\n" + "="*50)
print("Testing complete!")
print("="*50)