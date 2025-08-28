#!/usr/bin/env python3
"""Hypothesis property tests for optax - looking for real bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import math
import traceback
import numpy as np
import jax
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, settings, example
from hypothesis.extra import numpy as hnp

# Configure JAX
jax.config.update('jax_enable_x64', False)

print("Running Hypothesis property tests for optax...")
print("-" * 60)

# Bug hunt 1: safe_increment edge cases
print("\n1. Testing safe_increment for overflow protection...")

@given(st.integers())
@example(2147483647)  # int32 max
@example(-2147483648)  # int32 min  
@settings(max_examples=100)
def test_safe_increment_int32(value):
    """Test safe_increment with int32 values."""
    try:
        count = jnp.asarray(value, dtype=jnp.int32)
        result = optax.safe_increment(count)
        
        # Check no overflow
        assert not jnp.isinf(result) and not jnp.isnan(result)
        
        # Check behavior at max
        if value == 2147483647:
            assert result == 2147483647, f"At int32 max, got {result}"
        elif value < 2147483647:
            assert result == value + 1, f"Expected {value+1}, got {result}"
            
    except Exception as e:
        print(f"  ❌ ERROR with value {value}: {e}")
        return False
    return True

try:
    test_safe_increment_int32()
    print("  ✓ safe_increment int32 tests passed")
except AssertionError as e:
    print(f"  ❌ BUG FOUND in safe_increment: {e}")
    traceback.print_exc()

# Bug hunt 2: abs_sq with complex numbers
print("\n2. Testing abs_sq with complex arrays...")

@given(
    hnp.arrays(dtype=np.float32, shape=(5,), 
               elements=st.floats(min_value=-100, max_value=100, allow_nan=False)),
    hnp.arrays(dtype=np.float32, shape=(5,),
               elements=st.floats(min_value=-100, max_value=100, allow_nan=False))
)
@settings(max_examples=50)
def test_abs_sq_complex(real_part, imag_part):
    """Test abs_sq with complex numbers."""
    from optax._src.numerics import abs_sq
    
    try:
        z = jnp.asarray(real_part + 1j * imag_part)
        result = abs_sq(z)
        
        # Check result is real
        assert jnp.all(jnp.isreal(result)), "abs_sq should return real values"
        
        # Check result is non-negative
        assert jnp.all(result >= 0), "abs_sq should be non-negative"
        
        # Check correctness: |z|^2 = real^2 + imag^2
        expected = real_part**2 + imag_part**2
        if not jnp.allclose(result, expected, rtol=1e-5):
            raise AssertionError(f"abs_sq incorrect: got {result}, expected {expected}")
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        traceback.print_exc()
        return False
    return True

try:
    test_abs_sq_complex()
    print("  ✓ abs_sq complex tests passed")
except Exception as e:
    print(f"  ❌ BUG FOUND in abs_sq: {e}")

# Bug hunt 3: safe_norm gradient safety
print("\n3. Testing safe_norm with edge cases...")

@given(
    st.floats(min_value=1e-10, max_value=10.0, allow_nan=False)
)
@example(1e-6)
@example(0.0)
@settings(max_examples=50)
def test_safe_norm_zero_gradient(min_norm):
    """Test safe_norm handles zero vectors correctly."""
    try:
        # Zero vector case - critical for gradient safety
        x = jnp.zeros(5)
        result = optax.safe_norm(x, min_norm)
        
        # Must respect minimum
        assert result >= min_norm, f"safe_norm(zeros, {min_norm}) = {result} < min_norm"
        
        # Should equal min_norm for zero vector
        assert jnp.isclose(result, min_norm), f"Expected {min_norm}, got {result}"
        
    except Exception as e:
        print(f"  ❌ ERROR with min_norm={min_norm}: {e}")
        return False
    return True

try:
    test_safe_norm_zero_gradient()
    print("  ✓ safe_norm zero gradient tests passed")
except Exception as e:
    print(f"  ❌ BUG FOUND in safe_norm: {e}")

# Bug hunt 4: Testing apply_updates type preservation
print("\n4. Testing apply_updates type preservation...")

@given(
    hnp.arrays(dtype=np.float64, shape=(3,),
               elements=st.floats(min_value=-10, max_value=10, allow_nan=False)),
    hnp.arrays(dtype=np.float32, shape=(3,),
               elements=st.floats(min_value=-1, max_value=1, allow_nan=False))
)
@settings(max_examples=30)
def test_apply_updates_dtype(params64, updates32):
    """Test if apply_updates preserves parameter dtype."""
    try:
        params = jnp.asarray(params64, dtype=jnp.float64)
        updates = jnp.asarray(updates32, dtype=jnp.float32)
        
        result = optax.apply_updates(params, updates)
        
        # Check dtype is preserved from params, not updates
        assert result.dtype == params.dtype, f"dtype not preserved: got {result.dtype}, expected {params.dtype}"
        
        # Check calculation is correct
        expected = params + updates.astype(params.dtype)
        assert jnp.allclose(result, expected, rtol=1e-6)
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False
    return True

try:
    test_apply_updates_dtype()
    print("  ✓ apply_updates dtype preservation tests passed")
except Exception as e:
    print(f"  ❌ BUG FOUND in apply_updates: {e}")

# Bug hunt 5: incremental_update boundary values
print("\n5. Testing incremental_update with boundary step sizes...")

@given(
    hnp.arrays(dtype=np.float32, shape=(5,),
               elements=st.floats(min_value=-100, max_value=100, allow_nan=False)),
    hnp.arrays(dtype=np.float32, shape=(5,),
               elements=st.floats(min_value=-100, max_value=100, allow_nan=False)),
    st.floats(min_value=-0.1, max_value=1.1, allow_nan=False)  # Include outside [0,1]
)
@example(np.array([1.0]), np.array([2.0]), 0.0)
@example(np.array([1.0]), np.array([2.0]), 1.0)
@example(np.array([1.0]), np.array([2.0]), -0.1)  # Outside valid range
@example(np.array([1.0]), np.array([2.0]), 1.1)   # Outside valid range
@settings(max_examples=50)
def test_incremental_update_boundaries(new_val, old_val, step_size):
    """Test incremental_update with various step sizes."""
    try:
        new_jax = jnp.asarray(new_val)
        old_jax = jnp.asarray(old_val)
        
        result = optax.incremental_update(new_jax, old_jax, step_size)
        
        # The formula should work even for step_size outside [0,1]
        expected = step_size * new_jax + (1.0 - step_size) * old_jax
        
        if not jnp.allclose(result, expected, rtol=1e-5, atol=1e-7):
            raise AssertionError(
                f"incremental_update incorrect for step_size={step_size}\n"
                f"  Got: {result}\n"
                f"  Expected: {expected}"
            )
            
    except Exception as e:
        print(f"  ❌ ERROR with step_size={step_size}: {e}")
        return False
    return True

try:
    test_incremental_update_boundaries()
    print("  ✓ incremental_update boundary tests passed")
except Exception as e:
    print(f"  ❌ BUG FOUND in incremental_update: {e}")

# Bug hunt 6: global_norm with empty trees
print("\n6. Testing global_norm with edge cases...")

def test_global_norm_edges():
    """Test global_norm with various tree structures."""
    try:
        # Empty tree - should this work?
        try:
            result = optax.global_norm({})
            assert result == 0.0, f"global_norm({{}}) should be 0, got {result}"
            print("  ✓ global_norm handles empty dict")
        except:
            print("  ⚠ global_norm doesn't handle empty dict")
        
        # Single zero array
        result = optax.global_norm({'a': jnp.zeros(5)})
        assert jnp.isclose(result, 0.0), f"global_norm of zeros should be 0"
        print("  ✓ global_norm of zeros works")
        
        # Mix of positive and negative
        tree = {'a': jnp.array([-3.0, 4.0])}  # norm = 5
        result = optax.global_norm(tree)
        assert jnp.isclose(result, 5.0), f"Expected 5.0, got {result}"
        print("  ✓ global_norm with mixed signs works")
        
        # Very large values
        tree = {'a': jnp.array([1e20, 1e20])}
        result = optax.global_norm(tree)
        assert not jnp.isinf(result), "global_norm overflow with large values"
        print("  ✓ global_norm handles large values")
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        traceback.print_exc()

test_global_norm_edges()

# Bug hunt 7: periodic_update edge cases
print("\n7. Testing periodic_update...")

@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=1, max_value=10)
)
@example(0, 1)  # Edge case: step 0
@example(100, 0)  # Edge case: period 0 (should error?)
@settings(max_examples=30)
def test_periodic_update_logic(steps, period):
    """Test periodic_update update logic."""
    try:
        if period <= 0:
            # Should this error or have defined behavior?
            try:
                result = optax.periodic_update(
                    jnp.array([1.0]), 
                    jnp.array([2.0]), 
                    jnp.asarray(steps), 
                    period
                )
                print(f"  ⚠ periodic_update with period={period} didn't error")
            except:
                return True  # Expected to error
                
        new_val = jnp.array([1.0, 2.0])
        old_val = jnp.array([10.0, 20.0])
        
        result = optax.periodic_update(new_val, old_val, jnp.asarray(steps), period)
        
        should_update = (steps % period == 0)
        expected = new_val if should_update else old_val
        
        if not jnp.array_equal(result, expected):
            raise AssertionError(
                f"periodic_update wrong for steps={steps}, period={period}\n"
                f"  Should update: {should_update}\n"
                f"  Got: {result}\n"
                f"  Expected: {expected}"
            )
            
    except Exception as e:
        if period > 0:  # Only report errors for valid periods
            print(f"  ❌ ERROR with steps={steps}, period={period}: {e}")
            return False
    return True

try:
    test_periodic_update_logic()
    print("  ✓ periodic_update logic tests passed")
except Exception as e:
    print(f"  ❌ BUG FOUND in periodic_update: {e}")

print("\n" + "="*60)
print("Property testing complete!")
print("="*60)

# Summary
print("\nTested properties:")
print("1. safe_increment overflow protection")
print("2. abs_sq complex number handling")
print("3. safe_norm gradient safety at zero")
print("4. apply_updates dtype preservation")
print("5. incremental_update formula correctness")
print("6. global_norm edge cases")
print("7. periodic_update timing logic")