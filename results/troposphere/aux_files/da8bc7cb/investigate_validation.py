#!/usr/bin/env python3
"""Investigate when validation happens"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import managedblockchain

# Test with validation=False (default is True)
print("Test 1: Creating object with validation=False and empty string")
try:
    policy = managedblockchain.ApprovalThresholdPolicy(
        validation=False,
        ThresholdPercentage=''
    )
    print(f"Success! Created with ThresholdPercentage='': {policy.ThresholdPercentage}")
    print("This shows validation can be bypassed with validation=False")
except Exception as e:
    print(f"Failed: {e}")

print("\nTest 2: Creating object with validation=True (default) and empty string")
try:
    policy = managedblockchain.ApprovalThresholdPolicy(
        ThresholdPercentage=''
    )
    print(f"Success! Created with ThresholdPercentage='': {policy.ThresholdPercentage}")
except Exception as e:
    print(f"Failed as expected: {e}")

print("\nTest 3: Looking at what happens in to_dict()")
try:
    policy = managedblockchain.ApprovalThresholdPolicy(
        validation=False,
        ThresholdPercentage=''
    )
    print(f"Created with validation=False")
    print(f"Calling to_dict()...")
    result = policy.to_dict()
    print(f"to_dict() result: {result}")
except Exception as e:
    print(f"Error during to_dict(): {e}")