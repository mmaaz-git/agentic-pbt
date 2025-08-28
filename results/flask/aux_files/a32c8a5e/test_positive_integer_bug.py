#!/usr/bin/env python3
"""Test for potential bug in positive_integer validator"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import positive_integer

# Test whether 0 is considered a positive integer
print("Testing positive_integer validator:")
print("-" * 40)

test_cases = [
    (0, "Zero"),
    ("0", "String zero"),
    (1, "One"),
    (-1, "Negative one"),
]

for value, description in test_cases:
    print(f"\nTesting {description} ({value!r}):")
    try:
        result = positive_integer(value)
        print(f"  ✓ Accepted, returned: {result!r}")
    except ValueError as e:
        print(f"  ✗ Rejected with error: {e}")

print("\n" + "=" * 40)
print("Analysis:")
print("In mathematics, positive integers are > 0")
print("If 0 is accepted, this violates the mathematical definition")
print("This could be a bug depending on the intended semantics")