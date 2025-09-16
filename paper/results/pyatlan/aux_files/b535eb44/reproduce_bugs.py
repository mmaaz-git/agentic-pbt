#!/usr/bin/env python3
"""Reproduce the bugs found in pyatlan."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.utils import to_camel_case

# Bug 1: to_camel_case is not idempotent
print("Bug 1: to_camel_case idempotence issue")
print("=" * 50)
input1 = 'A A'
once = to_camel_case(input1)
twice = to_camel_case(once)
print(f"Input: '{input1}'")
print(f"First application: '{once}'")
print(f"Second application: '{twice}'")
print(f"Idempotent? {once == twice}")
print()

# Let's check a few more cases
test_cases = ['A A', 'B_B', 'C-C', 'Test Case', 'UPPER_CASE']
for test in test_cases:
    once = to_camel_case(test)
    twice = to_camel_case(once)
    print(f"Input: '{test}' -> Once: '{once}' -> Twice: '{twice}' -> Idempotent: {once == twice}")

print("\n" + "=" * 50)

# Bug 2: Unicode character handling
print("\nBug 2: Unicode character handling issue")
print("=" * 50)
input2 = 'ß'
result = to_camel_case(input2)
print(f"Input: '{input2}'")
print(f"Result: '{result}'")
print(f"Input lower: '{input2.lower()}'")
print(f"Result lower: '{result.lower()}'")
print(f"Characters preserved? {input2.lower() == result.lower()}")

# Test with more Unicode
unicode_tests = ['ß', 'Straße', 'café', 'naïve', 'Zürich']
for test in unicode_tests:
    result = to_camel_case(test)
    print(f"Input: '{test}' -> Result: '{result}'")