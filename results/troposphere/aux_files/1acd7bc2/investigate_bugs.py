#!/usr/bin/env python3
"""Investigate the bugs found in troposphere.appsync"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import appsync, validators
import math

print("=== Bug 1: Empty string title validation ===")
try:
    # Empty string should not be valid alphanumeric
    api = appsync.Api("", Name="TestApi")
    print(f"Created Api with empty title: {api.title}")
    print(f"Title is alphanumeric: {''.isalnum()}")  # This is False
    print("BUG CONFIRMED: Empty string accepted as valid title when it's not alphanumeric")
except ValueError as e:
    print(f"Correctly rejected: {e}")

print("\n=== Bug 2: Missing required properties ===")
try:
    # CognitoConfig has AwsRegion and UserPoolId as required
    config = appsync.CognitoConfig()  # No properties provided
    print("Created CognitoConfig without required properties")
    
    # Try to use it
    result = config.to_dict()
    print(f"to_dict succeeded: {result}")
except ValueError as e:
    print(f"Validation error at to_dict: {e}")
    print("This is inconsistent - object creation should fail if required props missing")

print("\n=== Bug 3: Integer validator with infinity ===")
try:
    # QueryDepthLimit uses integer validator
    api = appsync.GraphQLApi(
        "TestAPI",
        Name="TestAPI", 
        AuthenticationType="API_KEY",
        QueryDepthLimit=float('inf')
    )
    print(f"Created GraphQLApi with infinity QueryDepthLimit")
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("BUG CONFIRMED: integer validator crashes with infinity instead of rejecting gracefully")
except (TypeError, ValueError) as e:
    print(f"Handled gracefully: {e}")

print("\n=== Additional investigation ===")

# Check what the integer validator does
print("Testing integer validator directly:")
for value in [1, 1.5, float('inf'), float('-inf'), float('nan'), "123"]:
    try:
        result = validators.integer(value)
        print(f"  integer({value}) = {result}")
    except Exception as e:
        print(f"  integer({value}) raised {type(e).__name__}: {e}")

# Check title validation logic
print("\nTesting title validation:")
for title in ["", " ", "valid123", "has-hyphen", "has_underscore", None]:
    try:
        api = appsync.Api(title, Name="Test")
        print(f"  Title '{title}' accepted")
    except Exception as e:
        print(f"  Title '{title}' rejected: {e}")