#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Investigate required properties handling in troposphere classes"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import ivs

print("Testing required properties enforcement in PlaybackRestrictionPolicy:")

# According to the props definition, AllowedCountries and AllowedOrigins are required (True flag)
print("\nPlaybackRestrictionPolicy props:")
for prop_name, (prop_type, required) in ivs.PlaybackRestrictionPolicy.props.items():
    print(f"  {prop_name}: required={required}")

print("\nTest 1: Creating without AllowedCountries (required):")
try:
    policy = ivs.PlaybackRestrictionPolicy("TestPolicy", AllowedOrigins=["https://example.com"])
    print("BUG: Created successfully without required AllowedCountries!")
    print(f"  Policy dict: {policy.to_dict()}")
except (TypeError, ValueError) as e:
    print(f"Correctly failed: {e}")

print("\nTest 2: Creating without AllowedOrigins (required):")
try:
    policy = ivs.PlaybackRestrictionPolicy("TestPolicy", AllowedCountries=["US"])
    print("BUG: Created successfully without required AllowedOrigins!")
    print(f"  Policy dict: {policy.to_dict()}")
except (TypeError, ValueError) as e:
    print(f"Correctly failed: {e}")

print("\nTest 3: Creating with both required properties:")
try:
    policy = ivs.PlaybackRestrictionPolicy(
        "TestPolicy",
        AllowedCountries=["US", "CA"],
        AllowedOrigins=["https://example.com"]
    )
    print("Created successfully with both required properties")
    print(f"  Policy dict: {policy.to_dict()}")
except Exception as e:
    print(f"Unexpected error: {e}")

print("\nThe issue: Troposphere doesn't enforce required properties at object creation time.")
print("The 'required' flag in props is only used for CloudFormation template validation,")
print("not Python object validation.")