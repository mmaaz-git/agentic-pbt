#!/usr/bin/env python3
"""Focused tests to reproduce potential bugs in troposphere validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

print("Testing integer validator with bytes...")
test_cases = [
    b'123',
    b'0',
    b'-5',
    b'999'
]

for test in test_cases:
    try:
        result = validators.integer(test)
        print(f"  validators.integer({test!r}) = {result!r}")
        print(f"    int(result) = {int(result)}")
    except Exception as e:
        print(f"  validators.integer({test!r}) raised {type(e).__name__}: {e}")

print("\nTesting double validator with bytes...")
for test in test_cases:
    try:
        result = validators.double(test)
        print(f"  validators.double({test!r}) = {result!r}")
        print(f"    float(result) = {float(result)}")
    except Exception as e:
        print(f"  validators.double({test!r}) raised {type(e).__name__}: {e}")

print("\nTesting ELB name validator with Unicode characters...")
unicode_tests = [
    'Ö',      # Latin Extended
    'café',   # Accented character
    'π',      # Greek letter
    'test123' # ASCII for comparison
]

for test in unicode_tests:
    try:
        result = validators.elb_name(test)
        print(f"  validators.elb_name({test!r}) = {result!r}")
    except ValueError as e:
        print(f"  validators.elb_name({test!r}) raised ValueError: {e}")
        # Check if Python considers it alphanumeric
        if test[0].isalnum():
            print(f"    NOTE: Python's isalnum() returns True for '{test[0]}'")

print("\nChecking what Python's isalnum() considers alphanumeric...")
test_chars = ['a', 'A', '0', 'ñ', 'Ö', 'π', '中', 'א']
for char in test_chars:
    print(f"  '{char}'.isalnum() = {char.isalnum()}")