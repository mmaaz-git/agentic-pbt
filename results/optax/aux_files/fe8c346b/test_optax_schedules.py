#!/usr/bin/env python3
"""Test optax schedules for potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import math
import jax.numpy as jnp
import optax
from hypothesis import given, strategies as st, settings, example

print("Testing optax schedules for bugs...")
print("=" * 60)

# Test 1: polynomial_schedule with edge cases
print("\n1. Testing polynomial_schedule edge cases...")

# Test with transition_steps = 0 (should be constant)
schedule = optax.polynomial_schedule(
    init_value=1.0, end_value=0.1, power=2, transition_steps=0
)
print(f"  transition_steps=0:")
print(f"    schedule(0) = {schedule(0)}")
print(f"    schedule(100) = {schedule(100)}")
if schedule(0) != 1.0 or schedule(100) != 1.0:
    print("    ❌ BUG: Should be constant at init_value")
else:
    print("    ✓ Correctly returns constant init_value")

# Test with negative transition_begin
schedule = optax.polynomial_schedule(
    init_value=1.0, end_value=0.1, power=2, 
    transition_steps=10, transition_begin=-5
)
print(f"  transition_begin=-5:")
print(f"    schedule(0) = {schedule(0)}")
# Should treat as transition_begin=0 according to docs

# Test with power=0 (should be instant transition)
schedule = optax.polynomial_schedule(
    init_value=1.0, end_value=0.1, power=0, transition_steps=100
)
print(f"  power=0:")
for i in [0, 1, 50, 99, 100]:
    val = schedule(i)
    print(f"    schedule({i}) = {val}")
# With power=0, (1-t/T)^0 = 1 for t<T, so it should be init_value until the end

# Test 2: linear_schedule boundary conditions
print("\n2. Testing linear_schedule boundaries...")

schedule = optax.linear_schedule(
    init_value=1.0, end_value=0.0, transition_steps=100
)
print(f"  Linear from 1.0 to 0.0 over 100 steps:")
print(f"    schedule(0) = {schedule(0)} (should be 1.0)")
print(f"    schedule(50) = {schedule(50)} (should be 0.5)")
print(f"    schedule(100) = {schedule(100)} (should be 0.0)")
print(f"    schedule(200) = {schedule(200)} (should be 0.0)")

# Test with init > end
schedule = optax.linear_schedule(
    init_value=0.0, end_value=1.0, transition_steps=100
)
print(f"  Linear from 0.0 to 1.0 (increasing):")
print(f"    schedule(0) = {schedule(0)}")
print(f"    schedule(50) = {schedule(50)}")
print(f"    schedule(100) = {schedule(100)}")

# Test 3: cosine_decay_schedule
print("\n3. Testing cosine_decay_schedule...")

schedule = optax.cosine_decay_schedule(
    init_value=1.0, decay_steps=100
)
print(f"  Cosine decay from 1.0 over 100 steps:")
print(f"    schedule(0) = {schedule(0)} (should be 1.0)")
print(f"    schedule(50) = {schedule(50)}")
print(f"    schedule(100) = {schedule(100)} (should be close to 0)")
print(f"    schedule(200) = {schedule(200)} (what happens after decay_steps?)")

# Test 4: exponential_decay
print("\n4. Testing exponential_decay...")

schedule = optax.exponential_decay(
    init_value=1.0, transition_steps=10, decay_rate=0.5
)
print(f"  Exponential decay with rate 0.5 every 10 steps:")
for i in [0, 9, 10, 19, 20, 30]:
    val = schedule(i)
    print(f"    schedule({i}) = {val}")

# At step 10, should be 1.0 * 0.5 = 0.5
# At step 20, should be 1.0 * 0.5^2 = 0.25
if not math.isclose(float(schedule(10)), 0.5, rel_tol=1e-6):
    print("    ❌ BUG: At step 10, expected 0.5")
if not math.isclose(float(schedule(20)), 0.25, rel_tol=1e-6):
    print("    ❌ BUG: At step 20, expected 0.25")

# Test 5: piecewise_constant_schedule
print("\n5. Testing piecewise_constant_schedule...")

boundaries_and_scales = {
    10: 0.1,
    20: 0.01
}
schedule = optax.piecewise_constant_schedule(
    init_value=1.0, boundaries_and_scales=boundaries_and_scales
)
print(f"  Piecewise constant with boundaries at 10, 20:")
for i in [0, 9, 10, 19, 20, 30]:
    val = schedule(i)
    print(f"    schedule({i}) = {val}")

# Check values
if float(schedule(0)) != 1.0:
    print("    ❌ BUG: Initial value should be 1.0")
if not math.isclose(float(schedule(10)), 0.1, rel_tol=1e-6):
    print("    ❌ BUG: At step 10, should scale by 0.1")
if not math.isclose(float(schedule(20)), 0.001, rel_tol=1e-6):
    print("    ❌ BUG: At step 20, should scale by 0.01 (cumulative)")

# Test 6: Property test for schedule monotonicity
print("\n6. Property testing schedule behaviors...")

@given(
    init_value=st.floats(min_value=0.001, max_value=10.0, allow_nan=False),
    end_value=st.floats(min_value=0.0, max_value=10.0, allow_nan=False),
    power=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    transition_steps=st.integers(min_value=1, max_value=1000)
)
@settings(max_examples=50)
def test_polynomial_schedule_bounds(init_value, end_value, power, transition_steps):
    """Test that polynomial schedule stays within bounds."""
    schedule = optax.polynomial_schedule(
        init_value, end_value, power, transition_steps
    )
    
    # Check start and end values
    start_val = float(schedule(0))
    end_val = float(schedule(transition_steps))
    
    # Start should be init_value
    assert math.isclose(start_val, init_value, rel_tol=1e-5), \
        f"Start value {start_val} != init_value {init_value}"
    
    # End should be end_value
    assert math.isclose(end_val, end_value, rel_tol=1e-5), \
        f"End value {end_val} != end_value {end_value}"
    
    # Values should be bounded by min/max of init and end
    for step in [transition_steps // 4, transition_steps // 2, 3 * transition_steps // 4]:
        val = float(schedule(step))
        min_bound = min(init_value, end_value) - 1e-6
        max_bound = max(init_value, end_value) + 1e-6
        assert min_bound <= val <= max_bound, \
            f"Value {val} at step {step} outside bounds [{min_bound}, {max_bound}]"

try:
    test_polynomial_schedule_bounds()
    print("  ✓ polynomial_schedule bounds test passed")
except AssertionError as e:
    print(f"  ❌ BUG in polynomial_schedule: {e}")

# Test 7: join_schedules
print("\n7. Testing join_schedules...")

schedule1 = optax.constant_schedule(1.0)
schedule2 = optax.constant_schedule(0.1)
boundaries = [10]
joined = optax.join_schedules([schedule1, schedule2], boundaries)

print(f"  Join two constant schedules at step 10:")
for i in [0, 9, 10, 11, 20]:
    val = joined(i)
    print(f"    joined({i}) = {val}")

if float(joined(9)) != 1.0:
    print("    ❌ BUG: Before boundary should use first schedule")
if float(joined(10)) != 0.1:
    print("    ❌ BUG: At/after boundary should use second schedule")

print("\n" + "=" * 60)
print("Schedule testing complete!")