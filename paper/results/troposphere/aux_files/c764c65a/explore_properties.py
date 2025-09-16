#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
from troposphere.kafkaconnect import *
from troposphere import BaseAWSObject
from troposphere.validators import integer, boolean

# Test round-trip properties
print("=== Testing round-trip serialization ===")

# ScaleInPolicy
scale_in = ScaleInPolicy(CpuUtilizationPercentage=80)
dict_repr = scale_in.to_dict()
print(f"ScaleInPolicy to_dict: {dict_repr}")

# Can we create from dict?
print(f"ScaleInPolicy.from_dict method exists: {hasattr(ScaleInPolicy, 'from_dict')}")
if hasattr(ScaleInPolicy, 'from_dict'):
    try:
        recreated = ScaleInPolicy.from_dict("test", dict_repr)
        print(f"Recreated from dict: {recreated.to_dict()}")
    except Exception as e:
        print(f"Error recreating from dict: {e}")

# Test with edge cases for integer validator
print("\n=== Testing integer validator edge cases ===")
test_cases = [
    0,
    -1,
    1,
    100,
    999999999999999999999999999999,  # Very large int
    1.0,  # Float that's actually an int
    True,  # Boolean (which is int subclass in Python)
    False,
]

for val in test_cases:
    try:
        scale = ScaleInPolicy(CpuUtilizationPercentage=val)
        result = scale.to_dict()
        print(f"ScaleInPolicy(CpuUtilizationPercentage={repr(val)}) -> {result}")
    except Exception as e:
        print(f"ScaleInPolicy(CpuUtilizationPercentage={repr(val)}) raised {type(e).__name__}: {e}")

# Test AutoScaling with nested properties
print("\n=== Testing nested properties ===")
auto = AutoScaling(
    MaxWorkerCount=10,
    MinWorkerCount=1,
    McuCount=2,
    ScaleInPolicy=ScaleInPolicy(CpuUtilizationPercentage=20),
    ScaleOutPolicy=ScaleOutPolicy(CpuUtilizationPercentage=80)
)
print(f"AutoScaling to_dict: {auto.to_dict()}")

# Test required vs optional properties
print("\n=== Testing required vs optional properties ===")
print(f"ProvisionedCapacity props: {ProvisionedCapacity.props}")
# McuCount is optional (False), WorkerCount is required (True)

try:
    # Missing required field
    prov1 = ProvisionedCapacity()
    print(f"Created without required field: {prov1.to_dict()}")
except Exception as e:
    print(f"Error creating without required field: {e}")

try:
    # Only required field
    prov2 = ProvisionedCapacity(WorkerCount=5)
    print(f"Only required field: {prov2.to_dict()}")
except Exception as e:
    print(f"Error with only required field: {e}")

try:
    # Both fields
    prov3 = ProvisionedCapacity(WorkerCount=5, McuCount=2)
    print(f"Both fields: {prov3.to_dict()}")
except Exception as e:
    print(f"Error with both fields: {e}")

# Test the from_dict functionality
print("\n=== Testing from_dict in detail ===")
print(f"BaseAWSObject has from_dict: {hasattr(BaseAWSObject, 'from_dict')}")
if hasattr(BaseAWSObject, 'from_dict'):
    print(f"from_dict signature: {inspect.signature(BaseAWSObject.from_dict)}")
    
    # Try the from_dict method
    test_dict = {"CpuUtilizationPercentage": 50}
    try:
        obj = ScaleInPolicy.from_dict("TestPolicy", test_dict)
        print(f"Created from dict: {obj}")
        print(f"Title: {obj.title}")
        print(f"to_dict: {obj.to_dict()}")
    except Exception as e:
        print(f"Error: {e}")

# Look for validators property pattern
print("\n=== Exploring validator behavior ===")
# The integer validator accepts the value if int(x) doesn't raise
# But returns x unchanged - this could be a property to test

# Test values that int() accepts but might cause issues
edge_values = [
    "123",  # String that can be converted to int
    b"456",  # Bytes that can be converted to int
    True,   # Boolean (int subclass)
    False,
    1.0,    # Float with no fractional part
]

for val in edge_values:
    try:
        result = integer(val)
        print(f"integer({repr(val)}) = {repr(result)} (type: {type(result).__name__})")
        # Now test if it works in a property
        obj = ScaleInPolicy(CpuUtilizationPercentage=val)
        dict_val = obj.to_dict()["CpuUtilizationPercentage"]
        print(f"  In ScaleInPolicy.to_dict(): {repr(dict_val)} (type: {type(dict_val).__name__})")
    except Exception as e:
        print(f"integer({repr(val)}) error: {e}")