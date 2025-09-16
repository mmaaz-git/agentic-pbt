#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.pcaconnectorscep as pcaconnectorscep

# Test when validate_title is called
print("Creating Challenge with empty title...")
challenge = pcaconnectorscep.Challenge("", ConnectorArn="arn:test")
print(f"Challenge created. Title = {repr(challenge.title)}")

print("\nCalling to_dict()...")
try:
    result = challenge.to_dict()
    print("to_dict() succeeded")
    print(f"Result: {result}")
except Exception as e:
    print(f"to_dict() failed: {e}")

# Let's also check the initialization flow
print("\n\nChecking title during init with valid title...")
challenge2 = pcaconnectorscep.Challenge("ValidTitle", ConnectorArn="arn:test")
print(f"Title after init: {repr(challenge2.title)}")

# Check what happens with AWSProperty which doesn't require a title
print("\n\nTesting AWSProperty (no title required)...")
config = pcaconnectorscep.IntuneConfiguration(
    AzureApplicationId="app-id",
    Domain="example.com"
)
print(f"IntuneConfiguration title: {repr(config.title)}")
config_dict = config.to_dict()
print(f"IntuneConfiguration dict: {config_dict}")