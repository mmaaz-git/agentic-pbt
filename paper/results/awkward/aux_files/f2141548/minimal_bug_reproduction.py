#!/usr/bin/env python3
"""Minimal reproduction of forget_length() bug on scalar TypeTracerArrays."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward.typetracer as tt

# Create a scalar TypeTracerArray (0-dimensional)
scalar = tt.TypeTracerArray._new(np.dtype('float64'), shape=())

print(f"Original scalar shape: {scalar.shape}")
print(f"Original scalar ndim: {scalar.ndim}")

# Call forget_length() on the scalar
result = scalar.forget_length()

print(f"After forget_length() shape: {result.shape}")
print(f"After forget_length() ndim: {result.ndim}")

# The bug: forget_length() converts a scalar to a 1-dimensional array
assert result.shape == (tt.unknown_length,), "Bug confirmed: scalar became 1-d array!"
print("\nBUG CONFIRMED: forget_length() incorrectly changes scalar to 1-d array")