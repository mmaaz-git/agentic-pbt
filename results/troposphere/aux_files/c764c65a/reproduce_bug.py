#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import troposphere.kafkaconnect as kc

# Minimal reproduction of the bug
print("=== Bug Reproduction: Bytes values crash JSON serialization ===\n")

# Create a ScaleInPolicy with bytes value (which passes validation)
bytes_value = b'50'  # Bytes representation of "50"
print(f"Creating ScaleInPolicy with CpuUtilizationPercentage={repr(bytes_value)}")

policy = kc.ScaleInPolicy(CpuUtilizationPercentage=bytes_value)
print(f"✓ Object created successfully")

# Get dictionary representation
dict_repr = policy.to_dict()
print(f"✓ to_dict() succeeded: {dict_repr}")
print(f"  Type of value: {type(dict_repr['CpuUtilizationPercentage'])}")

# Try to serialize to JSON (as would be needed for CloudFormation)
print(f"\nAttempting JSON serialization (required for CloudFormation)...")
try:
    json_output = json.dumps(dict_repr)
    print(f"JSON output: {json_output}")
except TypeError as e:
    print(f"✗ JSON serialization failed with TypeError: {e}")
    print(f"\nThis is a BUG: The integer validator accepts bytes values,")
    print(f"but bytes cannot be serialized to JSON for CloudFormation templates.")

# Also demonstrate the issue with a complete AutoScaling configuration
print("\n=== Same issue in a complete AutoScaling configuration ===\n")

auto = kc.AutoScaling(
    MaxWorkerCount=10,
    MinWorkerCount=1, 
    McuCount=b'2',  # Using bytes here
    ScaleInPolicy=kc.ScaleInPolicy(CpuUtilizationPercentage=b'20'),
    ScaleOutPolicy=kc.ScaleOutPolicy(CpuUtilizationPercentage=80)
)

print("AutoScaling object created with bytes values")
auto_dict = auto.to_dict()
print(f"to_dict() result: {auto_dict}")

try:
    json_output = json.dumps(auto_dict)
    print(f"JSON output: {json_output}")
except TypeError as e:
    print(f"✗ JSON serialization failed: {e}")
    print("\nThe CloudFormation template cannot be generated due to bytes values.")