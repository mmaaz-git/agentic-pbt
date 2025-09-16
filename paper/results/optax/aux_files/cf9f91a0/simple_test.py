#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import jax
import jax.numpy as jnp
import optax.monte_carlo as mc
from optax._src import utils

# Test 1: Check shape invariant for score_function_jacobians
print("Test 1: Shape invariant for score_function_jacobians")
mean_array = jnp.array([1.0, 2.0])
log_std_array = jnp.array([0.5, 0.5])
params = (mean_array, log_std_array)
num_samples = 10

def simple_function(x):
    return jnp.sum(x ** 2)

rng = jax.random.PRNGKey(42)

jacobians = mc.score_function_jacobians(
    simple_function,
    params,
    utils.multi_normal,
    rng,
    num_samples
)

print(f"  Params shapes: {[p.shape for p in params]}")
print(f"  Jacobian shapes: {[j.shape for j in jacobians]}")
for i, param in enumerate(params):
    expected_shape = (num_samples,) + param.shape
    assert jacobians[i].shape == expected_shape, f"Shape mismatch!"
print("  ✓ Passed")

# Test 2: Moving average with decay=0
print("\nTest 2: Moving average baseline with decay=0")
def simple_func(x):
    return float(x[0])

_, _, update_state = mc.moving_avg_baseline(simple_func, decay=0.0, zero_debias=False)
state = (jnp.array(100.0), 0)

# Update with new value
samples = jnp.array([[50.0]])
state = update_state(None, samples, state)
print(f"  Initial: 100.0, New sample: 50.0, Result: {state[0]}")
assert jnp.allclose(state[0], 50.0), f"With decay=0, should equal last value"
print("  ✓ Passed")

# Test 3: Moving average with decay=1
print("\nTest 3: Moving average baseline with decay=1")
_, _, update_state = mc.moving_avg_baseline(
    simple_func, 
    decay=1.0, 
    zero_debias=False,
    use_decay_early_training_heuristic=False
)
state = (jnp.array(100.0), 0)
original = state[0]

# Update with new value
samples = jnp.array([[50.0]])
state = update_state(None, samples, state)
print(f"  Initial: 100.0, New sample: 50.0, Result: {state[0]}")
assert jnp.allclose(state[0], original), f"With decay=1, should never change"
print("  ✓ Passed")

# Test 4: Check for finite values
print("\nTest 4: Gradient estimators produce finite values")
mean_array = jnp.array([0.0, 0.0])
log_std_array = jnp.array([-1.0, -1.0])
params = (mean_array, log_std_array)

score_jacs = mc.score_function_jacobians(
    simple_function, params, utils.multi_normal, rng, 5
)
for jac in score_jacs:
    assert jnp.all(jnp.isfinite(jac)), "Non-finite values found!"
print("  ✓ Score function jacobians are finite")

pathwise_jacs = mc.pathwise_jacobians(
    simple_function, params, utils.multi_normal, rng, 5
)
for jac in pathwise_jacs:
    assert jnp.all(jnp.isfinite(jac)), "Non-finite values found!"
print("  ✓ Pathwise jacobians are finite")

measure_jacs = mc.measure_valued_jacobians(
    simple_function, params, utils.multi_normal, rng, 5
)
for jac in measure_jacs:
    assert jnp.all(jnp.isfinite(jac)), "Non-finite values found!"
print("  ✓ Measure valued jacobians are finite")

print("\n✅ All basic tests passed!")