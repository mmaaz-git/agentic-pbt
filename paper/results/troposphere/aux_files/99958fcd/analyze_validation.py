#!/usr/bin/env python3
"""Analyze validation behavior in troposphere.greengrassv2."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.greengrassv2 as ggv2

print("Analyzing validation in troposphere.greengrassv2...")
print("=" * 60)

# Analyze IoTJobAbortCriteria - has 4 required properties
print("\n1. Analyzing IoTJobAbortCriteria required properties:")
print("   Props definition:")
for prop_name, (prop_type, required) in ggv2.IoTJobAbortCriteria.props.items():
    req_str = "REQUIRED" if required else "optional"
    print(f"   - {prop_name}: {prop_type.__name__ if hasattr(prop_type, '__name__') else prop_type} ({req_str})")

# Test what happens when we omit required properties
print("\n2. Testing missing required properties:")
test_cases = [
    {
        "name": "All required props",
        "kwargs": {
            "Action": "CANCEL",
            "FailureType": "FAILED", 
            "MinNumberOfExecutedThings": 1,
            "ThresholdPercentage": 50.0
        },
        "should_work": True
    },
    {
        "name": "Missing Action",
        "kwargs": {
            "FailureType": "FAILED",
            "MinNumberOfExecutedThings": 1,
            "ThresholdPercentage": 50.0
        },
        "should_work": False
    },
    {
        "name": "Missing all required",
        "kwargs": {},
        "should_work": False
    }
]

for test in test_cases:
    try:
        obj = ggv2.IoTJobAbortCriteria(**test["kwargs"])
        # Try to serialize to trigger validation
        result = obj.to_dict()
        if test["should_work"]:
            print(f"   ✓ {test['name']}: Correctly created and serialized")
        else:
            print(f"   ✗ {test['name']}: Should have failed but succeeded!")
            print(f"      Result: {result}")
    except Exception as e:
        if not test["should_work"]:
            print(f"   ✓ {test['name']}: Correctly failed with {type(e).__name__}")
        else:
            print(f"   ✗ {test['name']}: Should have worked but failed: {e}")

# Check SystemResourceLimits validators
print("\n3. Testing SystemResourceLimits type validation:")
test_cases = [
    {"Cpus": 2.5, "Memory": 1024, "should_work": True, "name": "Valid types"},
    {"Cpus": "2.5", "Memory": "1024", "should_work": True, "name": "String numbers"},
    {"Cpus": "not_a_number", "Memory": 1024, "should_work": False, "name": "Invalid Cpus"},
    {"Cpus": 2.5, "Memory": "not_a_number", "should_work": False, "name": "Invalid Memory"},
]

for test in test_cases:
    try:
        kwargs = {k: v for k, v in test.items() if k not in ["should_work", "name"]}
        obj = ggv2.SystemResourceLimits(**kwargs)
        result = obj.to_dict()
        if test["should_work"]:
            print(f"   ✓ {test['name']}: Correctly created")
        else:
            print(f"   ✗ {test['name']}: Should have failed but succeeded!")
    except Exception as e:
        if not test["should_work"]:
            print(f"   ✓ {test['name']}: Correctly rejected: {type(e).__name__}")
        else:
            print(f"   ✗ {test['name']}: Should have worked but failed: {e}")

print("\n" + "=" * 60)
print("Validation analysis complete!")