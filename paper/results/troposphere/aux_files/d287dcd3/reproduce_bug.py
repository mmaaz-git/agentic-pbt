#!/usr/bin/env python3
"""Minimal reproduction of the boolean/integer validator bug."""

# Mock implementation (same as in cloudwatch.py)
def integer(x):
    return isinstance(x, int)

def double(x):
    return isinstance(x, (int, float))

# The bug: validators incorrectly accept boolean values
print("Bug demonstration:")
print(f"integer(True) = {integer(True)}   # Expected: False, Got: True")
print(f"integer(False) = {integer(False)}  # Expected: False, Got: True")
print(f"double(True) = {double(True)}    # Expected: False, Got: True")
print(f"double(False) = {double(False)}   # Expected: False, Got: True")

print("\nWhy this is a bug:")
print("1. In CloudFormation, boolean and integer are distinct types")
print("2. 'EvaluationPeriods: true' would fail in CloudFormation")
print("3. 'Threshold: false' would fail in CloudFormation")
print("4. The validators should match CloudFormation's validation")

print("\nPython's type hierarchy (root cause):")
print(f"issubclass(bool, int) = {issubclass(bool, int)}")
print(f"isinstance(True, int) = {isinstance(True, int)}")

print("\nCorrect implementation:")
def integer_fixed(x):
    return isinstance(x, int) and not isinstance(x, bool)

def double_fixed(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

print(f"integer_fixed(True) = {integer_fixed(True)}   # Correct!")
print(f"integer_fixed(5) = {integer_fixed(5)}       # Still works")
print(f"double_fixed(False) = {double_fixed(False)}   # Correct!")
print(f"double_fixed(3.14) = {double_fixed(3.14)}    # Still works")