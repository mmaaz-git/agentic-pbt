#!/usr/bin/env python3
"""Minimal reproduction of the integer validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import managedblockchain

# Test 1: Empty string for ThresholdPercentage should fail validation
print("Test 1: Empty string for integer field")
try:
    policy = managedblockchain.ApprovalThresholdPolicy(
        ThresholdPercentage=''
    )
    print(f"Created policy with ThresholdPercentage='': {policy.ThresholdPercentage}")
    print("Bug: Empty string was accepted for integer field!")
except ValueError as e:
    print(f"Correctly rejected empty string: {e}")

# Test 2: Non-numeric string should fail
print("\nTest 2: Non-numeric string for integer field")
try:
    policy = managedblockchain.ApprovalThresholdPolicy(
        ThresholdPercentage='not_a_number'
    )
    print(f"Created policy with ThresholdPercentage='not_a_number': {policy.ThresholdPercentage}")
    print("Bug: Non-numeric string was accepted for integer field!")
except ValueError as e:
    print(f"Correctly rejected non-numeric string: {e}")

# Test 3: Valid integer should work
print("\nTest 3: Valid integer")
try:
    policy = managedblockchain.ApprovalThresholdPolicy(
        ThresholdPercentage=50
    )
    print(f"Created policy with ThresholdPercentage=50: {policy.ThresholdPercentage}")
except ValueError as e:
    print(f"Unexpected error: {e}")