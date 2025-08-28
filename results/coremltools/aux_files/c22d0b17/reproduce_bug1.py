#!/usr/bin/env python3
"""Minimal reproduction for array_feature_extractor negative index bug"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.models import datatypes, array_feature_extractor

# Create an array with size 1
input_array = datatypes.Array(1)
input_features = [("input", input_array)]

# Try to extract with negative index
try:
    spec = array_feature_extractor.create_array_feature_extractor(
        input_features, "output", [-1]
    )
    print("No error raised - spec created successfully")
except AssertionError as e:
    print(f"AssertionError raised (expected): {e}")
except ValueError as e:
    print(f"ValueError raised (unexpected): {e}")
except Exception as e:
    print(f"Other exception raised: {type(e).__name__}: {e}")

# Also test if the assertion at line 56 actually works for positive out-of-bounds
try:
    spec = array_feature_extractor.create_array_feature_extractor(
        input_features, "output", [5]  # Out of bounds positive
    )
    print("No error for out-of-bounds positive index")
except AssertionError as e:
    print(f"AssertionError for positive out-of-bounds: {e}")