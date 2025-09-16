#!/usr/bin/env python3
"""Minimal reproduction of boolean validator empty string bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test with empty string
test_value = ''
print(f"Testing boolean validator with empty string: '{test_value}'")

try:
    result = boolean(test_value)
    print(f"Result: {result}")
except ValueError as e:
    print("ValueError raised (no message provided)")
    print("BUG: boolean validator raises bare ValueError for empty string instead of providing informative error")