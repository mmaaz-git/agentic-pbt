#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages/')

from azure.profiles import KnownProfiles
import re

# Test with a profile name containing regex special characters
profile_name = "?0"

try:
    result = KnownProfiles.from_name(profile_name)
    print(f"Unexpectedly succeeded: {result}")
except ValueError as e:
    error_message = str(e)
    print(f"Error message: {error_message}")
    
    # The error message is correct: "No profile called ?0"
    # But when using pytest.raises with match, we need to escape regex chars
    
    # This will fail because ? is a regex special char
    try:
        if not re.match(f"No profile called {profile_name}", error_message):
            print(f"Regex match failed without escaping")
    except:
        print(f"Regex pattern is invalid without escaping")
    
    # This works correctly
    escaped_pattern = f"No profile called {re.escape(profile_name)}"
    if re.match(escaped_pattern, error_message):
        print(f"Regex match succeeded with escaping")

# Test more regex special characters
special_chars_names = ["test.profile", "test*profile", "test+profile", "test[profile", "test(profile", "test$profile"]

for name in special_chars_names:
    try:
        KnownProfiles.from_name(name)
    except ValueError as e:
        # Check if error message is formatted correctly
        expected_msg = f"No profile called {name}"
        actual_msg = str(e)
        if actual_msg == expected_msg:
            print(f"✓ Error message correct for '{name}'")
        else:
            print(f"✗ Error message incorrect for '{name}': expected '{expected_msg}', got '{actual_msg}'")