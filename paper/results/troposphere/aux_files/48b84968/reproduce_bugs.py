#!/usr/bin/env python3
"""Minimal reproductions of discovered bugs"""

import sys
import math
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.apprunner as apprunner
from troposphere import validators

print("Bug 1: Title validation accepts Unicode alphanumeric but regex doesn't")
print("-" * 60)

# The character 'ª' is considered alphanumeric by Python but not by the regex
test_char = 'ª'  # Ordinal indicator character
print(f"Character: '{test_char}'")
print(f"Python isalnum(): {test_char.isalnum()}")
print(f"Expected to work based on isalnum?: Yes")

try:
    resource = apprunner.Service(test_char)
    print("Result: Success (created resource)")
except ValueError as e:
    print(f"Result: Failed with: {e}")

print("\nOther Unicode characters that trigger this:")
unicode_alphanums = ['¹', '²', '³', 'µ', 'º', '½', 'À', 'Á', 'ñ']
for char in unicode_alphanums:
    if char.isalnum():
        try:
            apprunner.Service(char)
            print(f"  '{char}': Success")
        except ValueError:
            print(f"  '{char}': Failed (but isalnum() is True)")

print("\n" + "=" * 60)
print("Bug 2: Integer validator crashes on float infinity")
print("-" * 60)

print("Testing validators.integer(float('inf'))...")
try:
    result = validators.integer(float('inf'))
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("Expected: ValueError with message 'inf is not a valid integer'")
except ValueError as e:
    print(f"ValueError (correct): {e}")

print("\nTesting validators.integer(float('-inf'))...")
try:
    result = validators.integer(float('-inf'))
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("Expected: ValueError with message '-inf is not a valid integer'")
except ValueError as e:
    print(f"ValueError (correct): {e}")