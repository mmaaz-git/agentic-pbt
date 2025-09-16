#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import jax
import jax.numpy as jnp
import numpy as np
import optax.monte_carlo as mc
from optax._src import utils

print("Bug hunting in optax.monte_carlo...")
print("=" * 50)

# Bug Hunt 1: Test measure_valued_jacobians with non-Gaussian distribution
print("\n1. Testing measure_valued_jacobians with non-Gaussian distribution")
print("-" * 40)

try:
    # Create a simple non-Gaussian distribution builder
    def non_gaussian_builder(*params):
        # This returns something that's not multi_normal
        class FakeDist:
            def sample(self, shape, key):
                return jax.random.uniform(key, shape)
        return FakeDist()
    
    mean = jnp.array([0.0])
    std = jnp.array([1.0])
    params = (mean, std)
    
    def test_func(x):
        return jnp.sum(x ** 2)
    
    rng = jax.random.PRNGKey(42)
    
    # This should raise ValueError according to the code
    result = mc.measure_valued_jacobians(
        test_func,
        params,
        non_gaussian_builder,  # Not utils.multi_normal!
        rng,
        10
    )
    print("  ❌ BUG FOUND: measure_valued_jacobians didn't raise ValueError for non-Gaussian distribution!")
    print(f"  Result: {result}")
    
except ValueError as e:
    print(f"  ✓ Correctly raised ValueError: {e}")
except Exception as e:
    print(f"  ⚠ Unexpected error: {type(e).__name__}: {e}")

# Bug Hunt 2: Test control_delta_method with multi-dimensional input
print("\n2. Testing control_delta_method Hessian shape assertion")
print("-" * 40)

try:
    # Function that could have non-2D Hessian
    def complex_function(x):
        # This function should work fine
        return jnp.sum(x ** 2) + jnp.sum(x ** 3)
    
    delta_cv, expected_delta, _ = mc.control_delta_method(complex_function)
    
    # Test with multi-dimensional mean
    mean = jnp.array([1.0, 2.0])
    log_std = jnp.array([0.5, 0.5])
    params = (mean, log_std)
    
    # Try computing delta
    sample = jnp.array([1.5, 2.5])
    cv_value = delta_cv(params, sample, None)
    print(f"  Control variate value: {cv_value}")
    
    # Try expected value
    exp_value = expected_delta(params, None)
    print(f"  Expected value: {exp_value}")
    
    print("  ✓ No issues with Hessian computation")
    
except AssertionError as e:
    print(f"  ❌ BUG FOUND: Assertion error in control_delta_method: {e}")
except Exception as e:
    print(f"  ⚠ Unexpected error: {type(e).__name__}: {e}")

# Bug Hunt 3: Test moving average baseline edge cases
print("\n3. Testing moving average baseline edge cases")
print("-" * 40)

try:
    def test_func(x):
        return float(x[0])
    
    # Test with extreme decay values
    for decay in [0.0, 1.0, -0.1, 1.1]:
        print(f"  Testing decay={decay}")
        _, _, update_state = mc.moving_avg_baseline(
            test_func, 
            decay=decay, 
            zero_debias=True,
            use_decay_early_training_heuristic=False
        )
        
        state = (jnp.array(0.0), 0)
        samples = jnp.array([[10.0]])
        
        # First update
        state = update_state(None, samples, state)
        
        if decay < 0 or decay > 1:
            print(f"    ⚠ No validation on decay value {decay}!")
        
        # Check for division by zero with zero_debias=True
        if decay == 1.0:
            # With decay=1 and zero_debias=True, we get division by (1 - 1^i) = 0
            if not jnp.isfinite(state[0]):
                print(f"    ❌ BUG FOUND: Non-finite value with decay=1.0 and zero_debias=True: {state[0]}")
            else:
                print(f"    Result: {state[0]}")
        else:
            print(f"    Result: {state[0]}")
            
except Exception as e:
    print(f"  ⚠ Unexpected error: {type(e).__name__}: {e}")

# Bug Hunt 4: Test coefficient estimation with edge cases
print("\n4. Testing control variate coefficient estimation edge cases")
print("-" * 40)

try:
    # Test with very small eps
    mean = jnp.array([0.0])
    log_std = jnp.array([0.0])
    params = (mean, log_std)
    
    def const_func(x):
        return 1.0  # Constant function
    
    rng = jax.random.PRNGKey(42)
    
    # With constant function, variance should be 0, leading to potential division issues
    coeffs = mc.estimate_control_variate_coefficients(
        const_func,
        mc.control_delta_method,
        mc.score_function_jacobians,
        params,
        utils.multi_normal,
        rng,
        num_samples=10,
        control_variate_state=None,
        eps=0.0  # Zero eps!
    )
    
    print(f"  Coefficients with eps=0: {coeffs}")
    
    if any(not jnp.isfinite(c) for c in coeffs):
        print("  ❌ BUG FOUND: Non-finite coefficients with eps=0")
    else:
        print("  ✓ Coefficients are finite even with eps=0")
        
except Exception as e:
    print(f"  ⚠ Error: {type(e).__name__}: {e}")

# Bug Hunt 5: Test with extreme parameter values
print("\n5. Testing gradient estimators with extreme values")
print("-" * 40)

try:
    # Very large mean and very small std
    mean = jnp.array([1e10])
    log_std = jnp.array([-10.0])  # std = exp(-10) ≈ 4.5e-5
    params = (mean, log_std)
    
    def test_func(x):
        return jnp.sum(x)
    
    rng = jax.random.PRNGKey(42)
    
    # Test pathwise gradients
    pathwise_jacs = mc.pathwise_jacobians(
        test_func, params, utils.multi_normal, rng, 5
    )
    
    print(f"  Mean jacobian: {jnp.mean(pathwise_jacs[0])}")
    print(f"  Std jacobian: {jnp.mean(pathwise_jacs[1])}")
    
    if any(not jnp.all(jnp.isfinite(jac)) for jac in pathwise_jacs):
        print("  ❌ BUG FOUND: Non-finite jacobians with extreme parameters")
    else:
        print("  ✓ Jacobians are finite even with extreme parameters")
        
except Exception as e:
    print(f"  ⚠ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("Bug hunting complete!")