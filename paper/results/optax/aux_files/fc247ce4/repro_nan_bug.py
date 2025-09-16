import optax
import numpy as np

# Bug: linear_onecycle_schedule returns NaN with transition_steps=1
transition_steps = 1
peak_value = 1.0
pct_start = 0.25
pct_final = 0.75

print("Creating linear_onecycle_schedule with transition_steps=1")
print(f"  transition_steps: {transition_steps}")
print(f"  peak_value: {peak_value}")
print(f"  pct_start: {pct_start}")
print(f"  pct_final: {pct_final}\n")

schedule = optax.linear_onecycle_schedule(
    transition_steps=transition_steps,
    peak_value=peak_value,
    pct_start=pct_start,
    pct_final=pct_final
)

print("Testing schedule at various steps:")
for step in [0, 1, 2]:
    result = schedule(step)
    print(f"Step {step}: {result}")
    if np.isnan(result):
        print("  ERROR: Result is NaN!")

print("\nRoot cause: Division by zero in piecewise_interpolate_schedule")
print("When boundaries are [0, 0, 0, 1], interval_sizes contains zeros")
print("This leads to division by zero when computing pct = (count - bounds[:-1]) / interval_sizes")