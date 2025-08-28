"""Bug reproduction: HVP crashes with scalar parameters"""
import jax
import jax.numpy as jnp
import optax.second_order

# Single scalar parameter
params = jnp.array(2.0)
inputs = jnp.array([[1.0], [2.0], [3.0]])
targets = jnp.array([2.0, 4.0, 6.0])

def loss_fn(p, x, t):
    pred = x.squeeze() * p
    return jnp.mean((pred - t) ** 2)

# Vector for HVP (scalar case)
v = jnp.array(1.0)

print(f"Parameter: {params} (shape: {params.shape})")
print(f"Vector v: {v} (shape: {v.shape})")

try:
    # This should work but crashes
    hvp_result = optax.second_order.hvp(loss_fn, v, params, inputs, targets)
    print(f"HVP result: {hvp_result}")
except Exception as e:
    print(f"\nBUG: HVP crashed with scalar parameter!")
    print(f"Error: {type(e).__name__}: {e}")
    print("\nThis function should handle scalar parameters correctly.")