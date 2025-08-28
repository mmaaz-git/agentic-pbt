#!/usr/bin/env python3
"""Minimal reproducers for bugs found in troposphere.iotwireless"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("=" * 60)
print("Bug 1: integer validator crashes on infinity")
print("=" * 60)

from troposphere.validators import integer

try:
    result = integer(float('inf'))
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("BUG CONFIRMED: integer validator doesn't handle infinity properly")

print("\n" + "=" * 60)
print("Bug 2: Title validation inconsistency with isalnum()")
print("=" * 60)

import troposphere.iotwireless as iotwireless

test_char = 'ª'
print(f"Character: {test_char}")
print(f"Python isalnum(): {test_char.isalnum()}")

try:
    obj = iotwireless.Destination(
        title=test_char,
        Expression="test",
        ExpressionType="RuleName",
        Name="TestDest"
    )
    print("Title accepted by troposphere")
except ValueError as e:
    print(f"Title rejected by troposphere: {e}")
    if test_char.isalnum():
        print("BUG CONFIRMED: Python's isalnum() says True but troposphere rejects it")

print("\n" + "=" * 60)
print("Bug 3: _from_dict fails without title")
print("=" * 60)

try:
    obj = iotwireless.Destination._from_dict(
        Expression="test",
        ExpressionType="RuleName",
        Name="TestDest"
    )
    print(f"Object created: {obj}")
except TypeError as e:
    print(f"TypeError: {e}")
    print("BUG CONFIRMED: _from_dict doesn't work without a title argument")