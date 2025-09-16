#!/usr/bin/env python3
"""
Minimal reproduction of division by zero bug in optax.monte_carlo.moving_avg_baseline
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import jax.numpy as jnp
import optax.monte_carlo as mc

# Define a simple function for the baseline
def simple_function(x):
    return float(x[0])

# Create moving average baseline with problematic parameters
_, _, update_state = mc.moving_avg_baseline(
    simple_function, 
    decay=1.0,  # Problematic: when decay=1.0
    zero_debias=True,  # Combined with zero_debias=True
    use_decay_early_training_heuristic=False  # And no heuristic override
)

# Initialize state: (value, iteration_count)
state = (jnp.array(0.0), 0)

# Create a sample
samples = jnp.array([[10.0]])

# Update state - this triggers division by zero
new_state = update_state(None, samples, state)

# The result will be inf or nan due to division by zero
print(f"Updated value: {new_state[0]}")
print(f"Is finite? {jnp.isfinite(new_state[0])}")

# Explanation:
# When decay=1.0 and zero_debias=True, the denominator becomes:
# 1 - decay^(i+1) = 1 - 1^1 = 1 - 1 = 0
# This causes division by zero, resulting in inf or nan