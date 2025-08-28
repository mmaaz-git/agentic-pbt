import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
import optax.losses

# Quick inline test
x = jnp.array([1.0, 2.0, 3.0])
y = jnp.array([1.5, 2.5, 3.5])
l2 = optax.losses.l2_loss(x, y)
squared = optax.losses.squared_error(x, y)
print(f"l2_loss: {l2}")
print(f"squared_error: {squared}")
print(f"0.5 * squared_error: {0.5 * squared}")
print(f"Are they equal? {jnp.allclose(l2, 0.5 * squared)}")