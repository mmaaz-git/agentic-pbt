#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages/')

from azure.profiles import KnownProfiles

# Test if the pre-defined profiles can be modified

# Get a known profile
profile = KnownProfiles.v2020_09_01_hybrid
profile_def = profile.value

# Get the internal dict
profile_dict = profile_def.get_profile_dict()

print(f"Original profile dict keys: {list(profile_dict.keys())}")

# Try to modify it
profile_dict["INJECTED_CLIENT"] = {None: "HACKED"}

# Check if it was modified
modified_dict = profile_def.get_profile_dict()
print(f"Modified profile dict keys: {list(modified_dict.keys())}")

if "INJECTED_CLIENT" in modified_dict:
    print("\n⚠️  BUG: Pre-defined KnownProfiles can be modified at runtime!")
    print(f"Injected value: {modified_dict['INJECTED_CLIENT']}")
    
    # This is a serious issue - it means any code can modify the "constant" profiles
    # that are supposed to be immutable definitions
    
    # Check if this affects other references to the same profile
    another_ref = KnownProfiles.v2020_09_01_hybrid
    another_dict = another_ref.value.get_profile_dict()
    
    if "INJECTED_CLIENT" in another_dict:
        print("The modification affects ALL references to this profile!")
else:
    print("Profile is protected from modification")