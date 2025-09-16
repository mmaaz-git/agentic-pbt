#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.trainers as trainers

print("Bug: UnigramTrainer accepts invalid shrinking_factor values")
print("-" * 60)
print("The shrinking_factor should be between 0 and 1 (exclusive on 0, inclusive on 1)")
print("It represents the factor by which to shrink vocabulary at each step.\n")

# Test invalid values that are accepted
test_values = [
    -1.0,    # Negative value - mathematically nonsensical
    -0.5,    # Negative value
    0.0,     # Zero - would eliminate everything
    1.5,     # Greater than 1 - would grow instead of shrink
    2.0,     # Way out of range
    100.0,   # Extremely out of range
]

for value in test_values:
    try:
        trainer = trainers.UnigramTrainer(shrinking_factor=value)
        print(f"shrinking_factor={value:6.1f} - ACCEPTED (Bug!)")
        # Verify the value is stored
        # Note: shrinking_factor is not exposed as an attribute, but we can see it in repr
        print(f"  Trainer repr: {trainer}")
    except (ValueError, TypeError) as e:
        print(f"shrinking_factor={value:6.1f} - Rejected: {e}")

print("\nExpected behavior: Values <= 0 or > 1 should be rejected with a ValueError")