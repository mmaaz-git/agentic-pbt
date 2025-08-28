#!/usr/bin/env python3
"""Minimal reproduction for Array accepting non-positive dimensions"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.models import datatypes

# Test with zero dimension
try:
    arr_zero = datatypes.Array(0)
    print(f"Array with dimension 0 created successfully: {arr_zero}")
    print(f"  Full tag: {arr_zero.full_tag}")
    print(f"  Num elements: {arr_zero.num_elements}")
except AssertionError as e:
    print(f"AssertionError for dimension 0: {e}")

# Test with negative dimension
try:
    arr_negative = datatypes.Array(-5)
    print(f"Array with dimension -5 created successfully: {arr_negative}")
    print(f"  Full tag: {arr_negative.full_tag}")
    print(f"  Num elements: {arr_negative.num_elements}")
except AssertionError as e:
    print(f"AssertionError for dimension -5: {e}")

# Test with multiple dimensions including zero
try:
    arr_multi = datatypes.Array(5, 0, 3)
    print(f"Array with dimensions (5, 0, 3) created successfully: {arr_multi}")
    print(f"  Full tag: {arr_multi.full_tag}")
    print(f"  Num elements: {arr_multi.num_elements}")
except AssertionError as e:
    print(f"AssertionError for dimensions (5, 0, 3): {e}")