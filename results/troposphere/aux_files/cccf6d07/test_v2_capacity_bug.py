import troposphere.rds as rds

# Test specific values that should expose the bug in validate_v2_capacity
print("Testing validate_v2_capacity half-step validation logic:")
print("="*60)

# These values should be INVALID (not half-step increments)
# but the current validation logic (capacity * 10 % 5 != 0) will accept them
invalid_but_accepted = [
    2.5,   # This IS valid (half-step)
    5.0,   # This IS valid (half-step) 
    7.5,   # This IS valid (half-step)
    10.0,  # This IS valid (half-step)
    12.5,  # This IS valid (half-step)
    # Let's try values that are NOT half-steps
    0.25,  # capacity * 10 = 2.5, 2.5 % 5 = 2.5 != 0 (correctly rejected)
    0.75,  # capacity * 10 = 7.5, 7.5 % 5 = 2.5 != 0 (correctly rejected)
    1.25,  # capacity * 10 = 12.5, 12.5 % 5 = 2.5 != 0 (correctly rejected)
    1.75,  # capacity * 10 = 17.5, 17.5 % 5 = 2.5 != 0 (correctly rejected)
    2.25,  # capacity * 10 = 22.5, 22.5 % 5 = 2.5 != 0 (correctly rejected)
]

# Wait, let me reconsider. The logic is: capacity * 10 % 5 != 0
# For half-steps like 0.5, 1.0, 1.5, 2.0, 2.5:
# 0.5 * 10 = 5, 5 % 5 = 0 (passes)
# 1.0 * 10 = 10, 10 % 5 = 0 (passes)
# 1.5 * 10 = 15, 15 % 5 = 0 (passes)
# 2.0 * 10 = 20, 20 % 5 = 0 (passes)

# For non-half-steps like 0.25, 0.75, 1.25:
# 0.25 * 10 = 2.5, 2.5 % 5 = 2.5 != 0 (fails - correct!)
# 0.75 * 10 = 7.5, 7.5 % 5 = 2.5 != 0 (fails - correct!)

# But wait, what about floating point precision issues?
# Let's test some edge cases with floating point arithmetic

test_values = [
    # Valid half-steps
    (0.5, True, "Valid half-step"),
    (1.0, True, "Valid half-step"),
    (1.5, True, "Valid half-step"),
    (2.0, True, "Valid half-step"),
    (2.5, True, "Valid half-step"),
    (127.5, True, "Valid half-step at upper bound"),
    (128.0, True, "Valid half-step at max"),
    
    # Invalid non-half-steps
    (0.25, False, "Quarter-step, should be rejected"),
    (0.75, False, "Three-quarter step, should be rejected"),
    (1.25, False, "Invalid fractional step"),
    (1.75, False, "Invalid fractional step"),
    (2.33, False, "Arbitrary decimal, should be rejected"),
    
    # Floating point precision edge cases
    (0.5000000000000001, True, "Slightly above 0.5 - FP precision"),
    (0.4999999999999999, True, "Slightly below 0.5 - FP precision"),
    (1.0000000000000002, True, "Slightly above 1.0 - FP precision"),
    (0.9999999999999998, True, "Slightly below 1.0 - FP precision"),
]

bugs_found = []

for value, should_pass, description in test_values:
    try:
        result = rds.validate_v2_capacity(value)
        if not should_pass:
            bugs_found.append(f"BUG: {value} ({description}) was accepted but should be rejected")
        else:
            print(f"✓ {value} ({description}) - correctly accepted")
    except ValueError as e:
        if should_pass and 0.5 <= value <= 128:
            bugs_found.append(f"BUG: {value} ({description}) was rejected but should be accepted")
        else:
            print(f"✓ {value} ({description}) - correctly rejected")

if bugs_found:
    print("\n" + "="*60)
    print("BUGS FOUND:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("\n" + "="*60)
    print("No bugs found in basic test cases")

# Now let's test the actual mathematical property more rigorously
print("\n" + "="*60)
print("Testing mathematical property of half-step validation:")

import math

def is_valid_half_step(x):
    """Check if x is a valid half-step (0.5, 1.0, 1.5, 2.0, ...)"""
    # A number is a half-step if x * 2 is an integer
    return abs(x * 2 - round(x * 2)) < 1e-10

def troposphere_check(x):
    """The check used by troposphere"""
    return (x * 10) % 5 == 0

# Test if these two checks are equivalent
print("\nComparing validation methods:")
test_points = [x / 100 for x in range(50, 300, 1)]  # 0.5 to 3.0 in 0.01 steps

discrepancies = []
for x in test_points:
    our_check = is_valid_half_step(x)
    their_check = troposphere_check(x)
    
    if our_check != their_check:
        discrepancies.append((x, our_check, their_check))

if discrepancies:
    print(f"Found {len(discrepancies)} discrepancies between expected and actual validation!")
    print("First 10 discrepancies:")
    for x, expected, actual in discrepancies[:10]:
        print(f"  x={x:.2f}: expected={expected}, troposphere={actual}")
else:
    print("Both validation methods agree on all test points")

# Test with Decimal for exact arithmetic
from decimal import Decimal

print("\n" + "="*60)
print("Testing with exact decimal arithmetic:")

def exact_troposphere_check(x):
    """Troposphere check using exact decimal arithmetic"""
    d = Decimal(str(x))
    return (d * 10) % 5 == 0

exact_discrepancies = []
for x in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 
          1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]:
    is_half = is_valid_half_step(x)
    tropos = troposphere_check(x)
    exact = exact_troposphere_check(x)
    
    print(f"x={x}: is_half_step={is_half}, tropos_check={tropos}, exact_check={exact}")
    
    if is_half != tropos:
        exact_discrepancies.append((x, is_half, tropos))