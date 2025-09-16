import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
import optax.contrib
from optax.contrib._complex_valued import _complex_to_real_pair, _real_pair_to_complex

# Test normalize with zero gradient
zero_grads = {'param': jnp.array([0.0, 0.0, 0.0])}
normalize_fn = optax.contrib.normalize()
state = normalize_fn.init(zero_grads)
normalized, _ = normalize_fn.update(zero_grads, state)
print("Zero gradient normalized:", normalized['param'])

# Test with non-zero gradient  
grads = {'param': jnp.array([3.0, 4.0])}
state2 = normalize_fn.init(grads)
normalized2, _ = normalize_fn.update(grads, state2)
norm = jnp.sqrt(jnp.sum(normalized2['param']**2))
print("Non-zero gradient norm after normalization:", float(norm))