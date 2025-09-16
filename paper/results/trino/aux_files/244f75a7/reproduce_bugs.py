#!/usr/bin/env python3
"""Reproduce the bugs found in trino.mapper module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.mapper import BooleanValueMapper, IntegerValueMapper

# Bug 1: BooleanValueMapper doesn't handle whitespace properly
print("Bug 1: BooleanValueMapper whitespace handling")
print("=" * 50)

boolean_mapper = BooleanValueMapper()

# These should work but don't
test_cases = [
    'TRUE ',   # trailing space
    ' TRUE',   # leading space
    'FALSE ',  # trailing space
    ' FALSE',  # leading space
    'true ',   # lowercase with trailing space
    ' false',  # lowercase with leading space
]

for test_value in test_cases:
    try:
        result = boolean_mapper.map(test_value)
        print(f"✓ '{test_value}' -> {result}")
    except ValueError as e:
        print(f"✗ '{test_value}' raises: {e}")

print("\nExpected: All values should be parsed after stripping whitespace")
print("Actual: ValueError is raised for strings with whitespace")

print("\n" + "=" * 50)
print("\nBug 2: IntegerValueMapper float string handling")
print("=" * 50)

integer_mapper = IntegerValueMapper()

# These fail even though they represent valid integers
float_strings = [
    '0.0',
    '1.0',
    '42.0',
    '-5.0',
    '100.0',
]

for test_value in float_strings:
    try:
        result = integer_mapper.map(test_value)
        print(f"✓ '{test_value}' -> {result}")
    except ValueError as e:
        print(f"✗ '{test_value}' raises: {e}")

print("\nExpected: Either parse as integer or provide clear error")
print("Actual: ValueError with confusing message")

# Additional test: The mapper accepts actual floats but not float strings
print("\n" + "=" * 50)
print("\nInconsistency: IntegerValueMapper handles float objects but not float strings")
print("=" * 50)

test_floats = [0.0, 1.0, 42.0, -5.0, 3.14]
for test_value in test_floats:
    try:
        # Direct float works
        result = integer_mapper.map(test_value)
        print(f"✓ Direct float {test_value} -> {result}")
    except Exception as e:
        print(f"✗ Direct float {test_value} raises: {e}")
    
    try:
        # Float string doesn't work
        result = integer_mapper.map(str(test_value))
        print(f"✓ String '{test_value}' -> {result}")
    except Exception as e:
        print(f"✗ String '{test_value}' raises: {e}")