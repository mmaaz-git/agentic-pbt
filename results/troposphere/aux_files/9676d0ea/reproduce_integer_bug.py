#!/usr/bin/env python3

import troposphere.signer as signer

# The integer function should reject non-integer floats
# but it incorrectly accepts them

test_values = [1.5, 42.7, -3.14, 100.001]

for val in test_values:
    try:
        result = signer.integer(val)
        print(f"Bug: integer({val}) returned {result} instead of raising ValueError")
        print(f"  int({result}) = {int(result)}, loses precision from original {val}")
    except ValueError as e:
        print(f"Correct: integer({val}) raised ValueError: {e}")