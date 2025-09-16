#!/usr/bin/env python3
"""Test to demonstrate potential mutability bug in trino.constants"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import trino.constants as constants

print("Demonstrating mutability issue in trino.constants")
print("="*60)

print("\nOriginal LENGTH_TYPES:", constants.LENGTH_TYPES)
print("Original PRECISION_TYPES:", constants.PRECISION_TYPES)
print("Original SCALE_TYPES:", constants.SCALE_TYPES)

# Simulate accidental mutation (could happen in user code)
print("\n[Simulating accidental mutation in user code...]")
constants.LENGTH_TYPES.append("corrupted")
constants.PRECISION_TYPES.clear()
constants.SCALE_TYPES.extend(["bad1", "bad2"])

print("\nAfter mutation:")
print("LENGTH_TYPES:", constants.LENGTH_TYPES)
print("PRECISION_TYPES:", constants.PRECISION_TYPES)
print("SCALE_TYPES:", constants.SCALE_TYPES)

# Now reimport to see if changes persist
print("\n[Re-importing module...]")
import importlib
importlib.reload(constants)

print("\nAfter reload:")
print("LENGTH_TYPES:", constants.LENGTH_TYPES)
print("PRECISION_TYPES:", constants.PRECISION_TYPES)
print("SCALE_TYPES:", constants.SCALE_TYPES)

print("\n" + "="*60)
print("ANALYSIS:")
print("The lists are mutable and can be corrupted during runtime.")
print("However, reimporting restores original values.")
print("This could cause bugs if code relies on these 'constants' being immutable.")