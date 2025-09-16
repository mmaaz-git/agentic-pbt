import troposphere.rds as rds
import sys

print("Demonstrating floating-point precision bug in validate_v2_capacity")
print("="*70)

# These values are mathematically equivalent to valid half-steps
# but have tiny floating-point representation errors

test_cases = [
    # Values that are extremely close to valid half-steps
    (1.0 + sys.float_info.epsilon, "1.0 + epsilon"),
    (1.0 - sys.float_info.epsilon, "1.0 - epsilon"),
    (0.5 + sys.float_info.epsilon, "0.5 + epsilon"),
    (2.5 - sys.float_info.epsilon * 2, "2.5 - 2*epsilon"),
    
    # Real-world floating point arithmetic results
    (0.1 + 0.1 + 0.1 + 0.1 + 0.1, "0.1 + 0.1 + 0.1 + 0.1 + 0.1 (should be 0.5)"),
    (0.1 * 10, "0.1 * 10 (should be 1.0)"),
    (0.3 + 0.2, "0.3 + 0.2 (should be 0.5)"),
    (1.4 + 0.1, "1.4 + 0.1 (should be 1.5)"),
]

print("\nTesting values that should be accepted as valid half-steps:")
bugs = []

for value, description in test_cases:
    print(f"\nTest: {description}")
    print(f"  Value: {value:.20f}")
    print(f"  Expected: Should be accepted (very close to half-step)")
    
    # Check if it's close to a half-step
    nearest_half_step = round(value * 2) / 2
    distance = abs(value - nearest_half_step)
    print(f"  Nearest half-step: {nearest_half_step}")
    print(f"  Distance: {distance:.2e}")
    
    try:
        result = rds.validate_v2_capacity(value)
        print(f"  Result: ✓ Accepted")
    except ValueError as e:
        print(f"  Result: ✗ Rejected with: {e}")
        if distance < 1e-10:  # Very close to a half-step
            bugs.append((value, description, str(e)))

# Now test the actual validation logic
print("\n" + "="*70)
print("Root cause analysis:")
print("\nThe validation uses: (capacity * 10) % 5 != 0")
print("This fails for floating-point values with tiny errors:")

for value, desc in [(0.5 + sys.float_info.epsilon, "0.5 + epsilon"),
                     (1.0 - sys.float_info.epsilon, "1.0 - epsilon")]:
    check_value = (value * 10) % 5
    print(f"\n{desc}:")
    print(f"  value * 10 = {value * 10:.20f}")
    print(f"  (value * 10) % 5 = {check_value:.20f}")
    print(f"  Is it != 0? {check_value != 0} (causes rejection)")

# Summary
if bugs:
    print("\n" + "="*70)
    print("BUG CONFIRMED: validate_v2_capacity has floating-point precision issues")
    print("\nAffected values:")
    for value, desc, error in bugs:
        print(f"  - {desc}: {value:.15f}")
    print("\nThis could affect real-world usage when:")
    print("  - Values are computed through arithmetic operations")
    print("  - Values are parsed from JSON/YAML with rounding")
    print("  - Values come from other systems with different precision")
else:
    print("\n" + "="*70)
    print("No precision bugs found (unexpected)")

# Demonstrate a realistic scenario
print("\n" + "="*70)
print("Realistic scenario that would fail:")
print("\nImagine scaling configuration computed dynamically:")

min_capacity = 0.1
scaling_steps = 5
step_size = 0.1

computed_capacity = min_capacity + (scaling_steps * step_size)
print(f"  min_capacity = {min_capacity}")
print(f"  scaling_steps = {scaling_steps}")
print(f"  step_size = {step_size}")
print(f"  computed_capacity = min_capacity + (scaling_steps * step_size)")
print(f"  computed_capacity = {computed_capacity:.20f}")
print(f"  Expected: 0.6 (valid half-step? No, but let's check 0.5))")

# Try with a value that should give us 0.5
scaling_steps = 4
computed_capacity = min_capacity + (scaling_steps * step_size)
print(f"\nWith scaling_steps = {scaling_steps}:")
print(f"  computed_capacity = {computed_capacity:.20f}")
print(f"  Expected: 0.5 (valid half-step)")

try:
    result = rds.validate_v2_capacity(computed_capacity)
    print(f"  Result: ✓ Accepted")
except ValueError as e:
    print(f"  Result: ✗ Rejected - {e}")
    print(f"  BUG: Computed value rejected due to floating-point arithmetic!")