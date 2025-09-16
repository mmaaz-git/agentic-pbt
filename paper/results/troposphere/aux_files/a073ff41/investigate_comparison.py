#!/usr/bin/env python3
"""Investigate why float 0.0 and 1.0 are accepted by boolean validator."""

# The issue is that Python's equality comparison between floats and ints
print("Testing Python's equality behavior:")
print(f"0.0 == 0: {0.0 == 0}")
print(f"1.0 == 1: {1.0 == 1}")
print(f"0.0 in [0]: {0.0 in [0]}")
print(f"1.0 in [1]: {1.0 in [1]}")
print(f"2.0 == 2: {2.0 == 2}")
print(f"2.0 in [2]: {2.0 in [2]}")

# But these shouldn't match
print(f"\n0.5 == 0: {0.5 == 0}")
print(f"0.5 == 1: {0.5 == 1}")
print(f"1.5 == 1: {1.5 == 1}")