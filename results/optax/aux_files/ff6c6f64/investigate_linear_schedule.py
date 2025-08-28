#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
import optax

# Test case from the failing test
init_val = 3.474085623540969e-07  # Float64 precision value
end_val = 1.0
transition_steps = 1

# Create the schedule
schedule_fn = optax.schedules.linear_schedule(
    init_value=init_val,
    end_value=end_val,
    transition_steps=transition_steps,
    transition_begin=0
)

# Get the initial value
start_val = schedule_fn(0)

print(f"Input init_val (float64): {init_val}")
print(f"  Type: {type(init_val)}")
print(f"  Precision: {init_val:.20e}")

print(f"\nSchedule returned value at step 0:")
print(f"  Value: {start_val}")
print(f"  Type: {type(start_val)}")
print(f"  JAX dtype: {start_val.dtype}")
print(f"  Precision: {float(start_val):.20e}")

print(f"\nDifference: {abs(float(start_val) - init_val):.20e}")

# Let's check if this is a JAX float32 conversion issue
float32_init = jnp.float32(init_val)
print(f"\nConverted to float32 directly:")
print(f"  Value: {float32_init}")
print(f"  Precision: {float(float32_init):.20e}")
print(f"  Matches schedule output: {float(float32_init) == float(start_val)}")

# Check if the schedule is actually working correctly given float32 precision
print(f"\nIs this a precision issue or a bug?")
print(f"  float32 can represent values with ~7 significant digits")
print(f"  Our input has value: {init_val:.7e}")
print(f"  float32 representation: {float(float32_init):.7e}")
print(f"  Are they close within float32 precision? {jnp.isclose(float32_init, init_val, rtol=1e-6)}")

# Let's also check the end value
end_step_val = schedule_fn(transition_steps)
print(f"\nEnd value check:")
print(f"  Expected: {end_val}")
print(f"  Got: {end_step_val}")
print(f"  Match: {jnp.isclose(end_step_val, end_val)}")