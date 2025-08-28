#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere
from troposphere import BaseAWSObject, AWSProperty, AWSObject
from troposphere.kafkaconnect import ScaleInPolicy, AutoScaling, Capacity

# Let's see the BaseAWSObject implementation
print("=== BaseAWSObject source ===")
try:
    source = inspect.getsource(BaseAWSObject)
    print(f"File: {inspect.getfile(BaseAWSObject)}")
    print(f"First 100 lines of source:")
    lines = source.split('\n')[:100]
    for i, line in enumerate(lines, 1):
        print(f"{i:3}: {line}")
except:
    print("Could not get source")

# Let's try to instantiate some objects and see how they work
print("\n=== Testing instantiation ===")

# Try creating a ScaleInPolicy
try:
    scale_in = ScaleInPolicy(CpuUtilizationPercentage=80)
    print(f"ScaleInPolicy created: {scale_in}")
    print(f"ScaleInPolicy.to_dict(): {scale_in.to_dict()}")
except Exception as e:
    print(f"Error creating ScaleInPolicy: {e}")

# Try with invalid value
try:
    scale_in_invalid = ScaleInPolicy(CpuUtilizationPercentage="not a number")
    print(f"ScaleInPolicy with string created: {scale_in_invalid}")
    print(f"ScaleInPolicy.to_dict(): {scale_in_invalid.to_dict()}")
except Exception as e:
    print(f"Error with invalid value: {e}")

# Test the validators
print("\n=== Testing validators ===")
from troposphere.validators import integer, boolean

test_values = [
    42,
    "42",
    42.0,
    42.5,
    "not a number",
    None,
    True,
    False,
    [],
    {},
]

for val in test_values:
    try:
        result = integer(val)
        print(f"integer({repr(val)}) = {repr(result)}")
    except Exception as e:
        print(f"integer({repr(val)}) raised {type(e).__name__}: {e}")

print("\n=== Testing boolean validator ===")
for val in test_values:
    try:
        result = boolean(val)
        print(f"boolean({repr(val)}) = {repr(result)}")
    except Exception as e:
        print(f"boolean({repr(val)}) raised {type(e).__name__}: {e}")