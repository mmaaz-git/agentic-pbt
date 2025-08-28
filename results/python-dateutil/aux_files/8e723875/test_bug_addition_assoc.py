#!/usr/bin/env python3
"""Test for addition associativity bug in relativedelta."""

from dateutil.relativedelta import relativedelta

# Bug: Addition is not associative due to _fix() normalization
rd1 = relativedelta(microseconds=1)
rd2 = relativedelta(seconds=-18, microseconds=-441891)
rd3 = relativedelta(seconds=-41, microseconds=-558109)

print("Testing associativity: (rd1 + rd2) + rd3 == rd1 + (rd2 + rd3)")
print(f"rd1 = {rd1}")
print(f"rd2 = {rd2}")
print(f"rd3 = {rd3}")
print()

# Left associative
temp = rd1 + rd2
print(f"rd1 + rd2 = {temp}")
left_assoc = temp + rd3
print(f"(rd1 + rd2) + rd3 = {left_assoc}")
print()

# Right associative
temp2 = rd2 + rd3
print(f"rd2 + rd3 = {temp2}")
right_assoc = rd1 + temp2
print(f"rd1 + (rd2 + rd3) = {right_assoc}")
print()

print(f"Are they equal? {left_assoc == right_assoc}")
print(f"Left minutes: {left_assoc.minutes}, Right minutes: {right_assoc.minutes}")
print(f"Left seconds: {left_assoc.seconds}, Right seconds: {right_assoc.seconds}")
print(f"Left microseconds: {left_assoc.microseconds}, Right microseconds: {right_assoc.microseconds}")

assert left_assoc == right_assoc, "Addition is not associative!"