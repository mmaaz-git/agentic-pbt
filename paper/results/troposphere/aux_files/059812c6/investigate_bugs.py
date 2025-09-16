"""Investigate the bugs found in troposphere.pinpoint"""
import sys
import math

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.pinpoint as pinpoint
from troposphere.validators import double

# Bug 1: Investigate NaN handling in double validator
print("=== Testing NaN handling in double validator ===")
try:
    nan_value = float('nan')
    result = double(nan_value)
    print(f"double(nan) returned: {result}")
    print(f"Type: {type(result)}")
    print(f"Is NaN: {math.isnan(result) if isinstance(result, float) else 'N/A'}")
    print(f"Result == nan_value: {result == nan_value}")
    print(f"Result is nan_value: {result is nan_value}")
except Exception as e:
    print(f"Error: {e}")

# Bug 2: Investigate App class initialization
print("\n=== Testing App class initialization ===")

# Try without title
try:
    app1 = pinpoint.App(Name="TestApp")
    print("App created without title - unexpected!")
except TypeError as e:
    print(f"Error without title: {e}")

# Try with title
try:
    app2 = pinpoint.App("MyApp", Name="TestApp")
    print(f"App created with title: {app2.title}")
    print(f"App Name property: {app2.properties.get('Name')}")
except Exception as e:
    print(f"Error with title: {e}")

# Bug 3: Investigate Campaign class initialization
print("\n=== Testing Campaign class initialization ===")

# Create a Schedule first
schedule = pinpoint.Schedule(Frequency="DAILY")

# Try without title
try:
    campaign1 = pinpoint.Campaign(
        ApplicationId="app-123",
        Name="TestCampaign",
        Schedule=schedule,
        SegmentId="seg-123"
    )
    print("Campaign created without title - unexpected!")
except TypeError as e:
    print(f"Error without title: {e}")

# Try with title
try:
    campaign2 = pinpoint.Campaign(
        "MyCampaign",
        ApplicationId="app-123",
        Name="TestCampaign",
        Schedule=schedule,
        SegmentId="seg-123"
    )
    print(f"Campaign created with title: {campaign2.title}")
    print(f"Campaign Name property: {campaign2.properties.get('Name')}")
except Exception as e:
    print(f"Error with title: {e}")

# Additional investigation: Check BaseAWSObject signature
print("\n=== Checking BaseAWSObject requirements ===")
from troposphere import BaseAWSObject
import inspect

sig = inspect.signature(BaseAWSObject.__init__)
print(f"BaseAWSObject.__init__ signature: {sig}")

# Check if title is optional
params = sig.parameters
title_param = params.get('title')
if title_param:
    print(f"Title parameter: {title_param}")
    print(f"Title has default? {title_param.default != inspect.Parameter.empty}")
    print(f"Title default value: {title_param.default}")

# Test double validator with infinity
print("\n=== Testing infinity handling in double validator ===")
for val in [float('inf'), float('-inf')]:
    try:
        result = double(val)
        print(f"double({val}) returned: {result}")
        print(f"Result == val: {result == val}")
        print(f"Result is val: {result is val}")
    except Exception as e:
        print(f"Error for {val}: {e}")