#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""
Bug 1: Parameter rejects empty string Description but accepts None
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Parameter

print("Testing Parameter with empty Description...")

# Test 1: None should be fine (omitting Description)
try:
    param1 = Parameter("Test1", Type="String")
    print("✓ Parameter with no Description works")
except Exception as e:
    print(f"✗ Parameter with no Description failed: {e}")

# Test 2: Explicit None should work too
try:
    param2 = Parameter("Test2", Type="String", Description=None)
    print("✗ Parameter with Description=None works (BUG: inconsistent with empty string)")
except Exception as e:
    print(f"✓ Parameter with Description=None rejected: {e}")

# Test 3: Empty string should be treated similarly
try:
    param3 = Parameter("Test3", Type="String", Description="")
    print("✓ Parameter with Description='' works")
except Exception as e:
    print(f"✗ Parameter with Description='' rejected (BUG if None is accepted): {e}")

# Test 4: Non-empty string should definitely work
try:
    param4 = Parameter("Test4", Type="String", Description="Valid description")
    print("✓ Parameter with valid Description works")
except Exception as e:
    print(f"✗ Parameter with valid Description failed: {e}")

print("\nConclusion: Inconsistent handling of None vs empty string for Description")