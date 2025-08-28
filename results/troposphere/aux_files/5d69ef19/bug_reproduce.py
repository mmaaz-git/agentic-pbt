#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python
"""Minimal bug reproducers for troposphere.lookoutmetrics validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean, integer

print("Testing boolean validator bug:")
print("=" * 50)

# Bug 1: boolean() accepts float 0.0 and returns False instead of raising ValueError
try:
    result = boolean(0.0)
    print(f"boolean(0.0) = {result}")
    print(f"Type: {type(result)}")
    print("BUG: Expected ValueError, but got False!")
except ValueError:
    print("Correctly raised ValueError for 0.0")

print("\nAlso accepts 1.0:")
try:
    result = boolean(1.0)
    print(f"boolean(1.0) = {result}")
    print(f"Type: {type(result)}")
    print("BUG: Expected ValueError, but got True!")
except ValueError:
    print("Correctly raised ValueError for 1.0")

print("\n" + "=" * 50)
print("Testing integer validator bug:")
print("=" * 50)

# Bug 2: integer() accepts non-integer floats without validation
try:
    result = integer(0.5)
    print(f"integer(0.5) = {result}")
    print(f"Type: {type(result)}")
    print("BUG: Expected ValueError for non-integer float 0.5!")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\nAlso accepts 3.14:")
try:
    result = integer(3.14)
    print(f"integer(3.14) = {result}")
    print("BUG: Expected ValueError for non-integer float 3.14!")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\nCompare with Python's int() behavior:")
print(f"int(0.5) = {int(0.5)} (truncates)")
print(f"int(3.14) = {int(3.14)} (truncates)")

print("\n" + "=" * 50)
print("Summary:")
print("=" * 50)
print("1. boolean() incorrectly accepts float values 0.0 and 1.0")
print("2. integer() accepts non-integer floats without proper validation")
print("\nThese bugs violate the documented type constraints of the validators.")