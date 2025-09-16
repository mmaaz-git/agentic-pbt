#!/usr/bin/env python3
"""Test more float edge cases with boolean validator."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

test_values = [0.0, 1.0, 2.0, -0.0, 0.5, 1.5, float('inf'), -1.0]

for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({value}) = {result} (BUG - should raise ValueError)")
    except ValueError:
        print(f"boolean({value}) correctly raised ValueError")