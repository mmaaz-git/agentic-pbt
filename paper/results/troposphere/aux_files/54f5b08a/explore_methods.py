#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.panorama as panorama

# Let's get the source of to_dict and from_dict methods
print("=== Exploring to_dict method ===")
try:
    source = inspect.getsource(panorama.ApplicationInstance.to_dict)
    print(f"to_dict source:\n{source[:1000]}")
except:
    print("Could not get source directly, checking parent class")
    try:
        BaseAWSObject = panorama.AWSObject.__bases__[0]
        source = inspect.getsource(BaseAWSObject.to_dict)
        print(f"BaseAWSObject.to_dict source:\n{source[:1000]}")
    except Exception as e:
        print(f"Error: {e}")

print("\n=== Exploring from_dict method ===")
try:
    source = inspect.getsource(panorama.ApplicationInstance.from_dict)
    print(f"from_dict source:\n{source[:1000]}")
except:
    print("Could not get source directly, checking parent class")
    try:
        BaseAWSObject = panorama.AWSObject.__bases__[0]
        source = inspect.getsource(BaseAWSObject.from_dict)
        print(f"BaseAWSObject.from_dict source:\n{source[:1000]}")
    except Exception as e:
        print(f"Error: {e}")

# Test creating an object and converting to dict
print("\n=== Testing object creation and conversion ===")
app = panorama.ApplicationInstance(
    "TestApp",
    DefaultRuntimeContextDevice="test-device"
)
print(f"Created ApplicationInstance: {app}")
print(f"to_dict result: {app.to_dict()}")

# Test with ManifestPayload
payload = panorama.ManifestPayload(PayloadData="test-data")
print(f"\nCreated ManifestPayload: {payload}")
print(f"to_dict result: {payload.to_dict()}")