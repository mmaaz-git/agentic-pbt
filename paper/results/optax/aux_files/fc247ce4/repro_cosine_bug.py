import optax
import jax.numpy as jnp

# Bug 2: Cosine decay bounds violation
init_value = 3.0
decay_steps = 1
alpha = 0.25226975859634654
exponent = 1.0

schedule = optax.cosine_decay_schedule(
    init_value=init_value,
    decay_steps=decay_steps,
    alpha=alpha,
    exponent=exponent
)

# Expected bounds according to documentation
min_value = alpha * init_value
max_value = init_value

print(f"Expected minimum value: {min_value}")
print(f"Expected maximum value: {max_value}")

# Test at various points
test_points = [0, 1, 2, 100]
for count in test_points:
    result = schedule(count)
    print(f"\nAt count={count}: {result}")
    print(f"  Is within bounds? {min_value <= result <= max_value}")
    if result < min_value:
        print(f"  VIOLATION: Result {result} < min_value {min_value}")
        print(f"  Difference: {min_value - result}")