"""Bug reproduction: HVP returns dict instead of array for nested params"""
import jax
import jax.numpy as jnp
import optax.second_order

# Nested parameter structure
params = {
    'weight': jnp.array([[1.0, 2.0]]),
    'bias': jnp.array([0.5])
}

inputs = jnp.array([[1.0, 0.5], [0.5, 1.0]])
targets = jnp.array([1.5, 2.0])

def loss_fn(params, inputs, targets):
    predictions = jnp.dot(inputs, params['weight'].T).squeeze() + params['bias']
    return jnp.mean((predictions - targets) ** 2)

# Get parameter size
from jax import flatten_util
flat_params, unflatten = flatten_util.ravel_pytree(params)
param_size = flat_params.size

# Create a vector for HVP
v = jnp.ones(param_size)

print(f"Parameter size: {param_size}")
print(f"Vector v shape: {v.shape}")

# Call HVP
hvp_result = optax.second_order.hvp(loss_fn, v, params, inputs, targets)

print(f"\nExpected: Array of shape ({param_size},)")
print(f"Got: {type(hvp_result)} = {hvp_result}")

if isinstance(hvp_result, dict):
    print("\nBUG: HVP returned a dict instead of a flattened array!")
    print("This violates the documented return type: 'An Array'")
else:
    print(f"Result shape: {hvp_result.shape}")