#!/usr/bin/env python3
"""Test the impact of the validator bugs on actual troposphere usage"""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.msk as msk

# Test 1: Float passed to boolean property
print("Test 1: VpcConnectivityIam with float for Enabled")
try:
    iam = msk.VpcConnectivityIam(Enabled=0.0)
    result = iam.to_dict()
    print(f"Result: {result}")
    print(f"Type of Enabled: {type(result['Enabled'])}")
    print()
except Exception as e:
    print(f"Error: {e}\n")

# Test 2: Float passed to integer property  
print("Test 2: ConfigurationInfo with float for Revision")
try:
    config = msk.ConfigurationInfo(
        Arn="arn:aws:kafka:us-east-1:123456789012:configuration/test",
        Revision=123.0
    )
    result = config.to_dict()
    print(f"Result: {result}")
    print(f"Type of Revision: {type(result['Revision'])}")
    print(f"JSON output: {json.dumps(result)}")
    print()
except Exception as e:
    print(f"Error: {e}\n")

# Test 3: Non-integer float to integer property
print("Test 3: ConfigurationInfo with non-integer float")
try:
    config = msk.ConfigurationInfo(
        Arn="arn:aws:kafka:us-east-1:123456789012:configuration/test",
        Revision=123.5
    )
    result = config.to_dict()
    print(f"Result: {result}")
    print(f"JSON output: {json.dumps(result)}")
except Exception as e:
    print(f"Error: {e}")