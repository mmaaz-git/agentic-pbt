#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages/')

from azure.profiles import ProfileDefinition

# Demonstrate the mutability bug in ProfileDefinition

# Create a profile dict
original_dict = {
    "azure.test.Client": {
        None: "2021-01-01",
        "operation1": "2020-01-01"
    }
}

# Create a ProfileDefinition with this dict
profile = ProfileDefinition(original_dict, "test-profile")

# Get the dict back
returned_dict = profile.get_profile_dict()

print(f"Original dict: {original_dict}")
print(f"Returned dict: {returned_dict}")
print(f"Are they the same object? {returned_dict is original_dict}")

# Modify the returned dict
returned_dict["azure.test.Client"]["operation2"] = "2019-01-01"

# Check if the internal dict was modified
internal_dict = profile.get_profile_dict()
print(f"\nAfter modifying returned dict:")
print(f"Internal dict: {internal_dict}")
print(f"Original dict: {original_dict}")

# This shows that ProfileDefinition doesn't protect its internal state
# External code can modify the profile definition after creation

# Even worse, modifying the original dict also changes the profile
original_dict["azure.test.Client"]["operation3"] = "2018-01-01"
print(f"\nAfter modifying original dict:")
print(f"Internal dict: {profile.get_profile_dict()}")

# This is a violation of encapsulation and could lead to bugs where
# profile definitions are unexpectedly modified during runtime