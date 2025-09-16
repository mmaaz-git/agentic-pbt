import optax
import jax.numpy as jnp

# Bug 1: Polynomial schedule boundary precision issue
init_value = 1.04296875
end_value = 65538.0
power = 1.0
transition_steps = 1
transition_begin = 1

schedule = optax.polynomial_schedule(
    init_value=init_value,
    end_value=end_value,
    power=power,
    transition_steps=transition_steps,
    transition_begin=transition_begin
)

# Test at transition_begin - 1  
result_before = schedule(0)
print(f"Result at count=0 (before transition): {result_before}")
print(f"Expected init_value: {init_value}")
print(f"Type of result: {type(result_before)}, dtype: {result_before.dtype}")
print(f"Type of init_value: {type(init_value)}")
print(f"Are they equal? {result_before == init_value}")
print(f"Difference: {float(result_before) - init_value}")

# Test at transition_begin
result_at_begin = schedule(1)
print(f"\nResult at count=1 (at transition_begin): {result_at_begin}")
print(f"Expected init_value: {init_value}")
print(f"Difference: {float(result_at_begin) - init_value}")

# Issue: When init_value is a Python float with higher precision,
# but JAX converts it to float32, precision is lost