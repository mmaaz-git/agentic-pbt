import optax

# Bug: exponential_decay violates upper bound when decay_rate > 1 (growth)
init_value = 2.0
transition_steps = 3
decay_rate = 9.0
end_value = 64.68065431345092

schedule = optax.exponential_decay(
    init_value=init_value,
    transition_steps=transition_steps,
    decay_rate=decay_rate,
    transition_begin=0,
    staircase=False,
    end_value=end_value
)

print(f"Initial value: {init_value}")
print(f"Decay rate (>1, so growth): {decay_rate}")
print(f"End value (should be upper bound): {end_value}")
print(f"Transition steps: {transition_steps}\n")

for step in range(10):
    result = float(schedule(step))
    print(f"Step {step}: {result:.10f}")
    if result > end_value:
        print(f"  VIOLATION: {result} > {end_value} (diff: {result - end_value})")