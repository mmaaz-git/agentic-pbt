#!/usr/bin/env python3
"""Simple test to check for bugs in isort.main"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.main
from isort.settings import Config

print("Testing isort.main for bugs...")

# Bug Test 1: Check if wrap_length validation works correctly
print("\n[BUG CHECK 1] Testing wrap_length > line_length...")
try:
    # This should raise ValueError
    config = Config(line_length=50, wrap_length=100)
    print("BUG FOUND: Config accepted wrap_length > line_length without raising ValueError!")
except ValueError as e:
    if "wrap_length must be set lower than or equal to line_length" in str(e):
        print("✓ Correctly rejected wrap_length > line_length")
    else:
        print(f"Unexpected error: {e}")

# Bug Test 2: Check parse_args with mutually exclusive flags
print("\n[BUG CHECK 2] Testing mutually exclusive --float-to-top flags...")
try:
    result = isort.main.parse_args(["--float-to-top", "--dont-float-to-top"])
    print("BUG FOUND: parse_args accepted both --float-to-top and --dont-float-to-top!")
except SystemExit as e:
    print("✓ Correctly rejected mutually exclusive flags")

# Bug Test 3: Check multi_line_output with invalid integer
print("\n[BUG CHECK 3] Testing multi_line_output with out-of-range integer...")
try:
    # WrapModes should only have values 0-12 based on the number of wrap functions
    result = isort.main.parse_args(["--multi-line", "999"])
    if "multi_line_output" in result:
        print(f"Result: {result['multi_line_output']}")
        print("Potential issue: Accepted very large multi_line_output value")
except (ValueError, KeyError) as e:
    print(f"✓ Correctly rejected invalid multi_line_output: {e}")

# Bug Test 4: Check _preconvert with edge cases
print("\n[BUG CHECK 4] Testing _preconvert with various types...")
test_cases = [
    (set([1, 2, 3]), "set"),
    (frozenset([4, 5, 6]), "frozenset"),
    ({"a": 1}, "dict"),
    (lambda x: x, "function"),
]

for value, desc in test_cases:
    try:
        result = isort.main._preconvert(value)
        print(f"✓ _preconvert({desc}) = {result}")
    except TypeError as e:
        print(f"✓ _preconvert({desc}) raised TypeError: {e}")

# Bug Test 5: Check Config with edge case py_version
print("\n[BUG CHECK 5] Testing Config py_version validation...")
invalid_versions = ["1", "4", "python3", "3.10", ""]
for version in invalid_versions:
    try:
        config = Config(py_version=version)
        print(f"Potential issue: Config accepted py_version='{version}'")
    except ValueError as e:
        print(f"✓ Correctly rejected py_version='{version}'")

# Bug Test 6: Test parse_args with negative line lengths
print("\n[BUG CHECK 6] Testing parse_args with negative line_length...")
try:
    result = isort.main.parse_args(["--line-length", "-10"])
    print(f"Potential issue: parse_args accepted negative line_length: {result.get('line_length')}")
    # Try to create Config with this
    try:
        config = Config(line_length=-10)
        print("BUG: Config accepted negative line_length!")
    except Exception as e:
        print(f"Config rejected negative line_length: {e}")
except Exception as e:
    print(f"parse_args rejected negative line_length: {e}")

# Bug Test 7: Test parse_args with contradictory wrap_length settings
print("\n[BUG CHECK 7] Testing contradictory wrap_length settings...")
result = isort.main.parse_args(["--line-length", "50", "--wrap-length", "100"])
print(f"parse_args result: line_length={result.get('line_length')}, wrap_length={result.get('wrap_length')}")
try:
    config = Config(**result)
    print(f"BUG FOUND: Config accepted wrap_length={result.get('wrap_length')} > line_length={result.get('line_length')}!")
except ValueError as e:
    print(f"✓ Config correctly rejected the contradictory settings: {e}")

print("\n" + "="*60)
print("Bug checking complete!")