#!/usr/bin/env python3
"""Minimal reproduction of linear_schedule precision bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
import optax

# Bug: linear_schedule doesn't preserve init_value at step 0 for small values
init_val = 3.474085623540969e-07
end_val = 1.0
transition_steps = 1

schedule_fn = optax.schedules.linear_schedule(
    init_value=init_val,
    end_value=end_val,
    transition_steps=transition_steps,
    transition_begin=0
)

result = schedule_fn(0)
expected = init_val

print("Bug: linear_schedule doesn't preserve init_value at step 0")
print(f"  init_value:      {init_val:.15e}")
print(f"  schedule_fn(0):  {float(result):.15e}")
print(f"  Difference:      {abs(float(result) - init_val):.15e}")
print(f"  Expected equal?: True")
print(f"  Actually equal?: {float(result) == init_val}")

# Let's trace through the computation manually
print("\nManual computation trace:")
count = 0
transition_begin = 0
count_clipped = jnp.clip(count - transition_begin, 0, transition_steps)
frac = 1 - count_clipped / transition_steps
result_manual = (init_val - end_val) * (frac**1) + end_val

print(f"  count_clipped: {count_clipped}")
print(f"  frac: {frac}")
print(f"  (init - end): {init_val - end_val}")
print(f"  (init - end) * frac: {(init_val - end_val) * float(frac)}")
print(f"  result: {result_manual}")

# The issue is that (init - end) * frac + end != init when init is very small
# and end is large, due to float32 precision loss
print("\nRoot cause analysis:")
print(f"  When init_val << end_val, the computation")
print(f"  (init_val - end_val) * 1.0 + end_val")
print(f"  = {init_val} - {end_val} + {end_val}")
print(f"  loses precision because subtracting and adding back a large value")
print(f"  relative to init_val causes float32 rounding errors.")