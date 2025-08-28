#!/usr/bin/env python3
"""Check if empty string bypasses title validation - critical bug test"""

import sys
import os

# Add the troposphere path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re

# First, let's verify what the regex actually does
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("Regex validation check:")
print(f"Empty string matches regex: {bool(valid_names.match(''))}")
print(f"Single letter matches regex: {bool(valid_names.match('A'))}")
print(f"Alphanumeric matches regex: {bool(valid_names.match('Test123'))}")
print(f"With hyphen matches regex: {bool(valid_names.match('Test-123'))}")

print("\n" + "="*50 + "\n")

# Now test with troposphere
import troposphere.finspace as finspace

print("Testing empty string as Environment title:")
try:
    # Attempt to create Environment with empty title
    env = finspace.Environment("", Name="TestEnvironment")
    
    # If we get here, empty string was accepted
    print("RESULT: Empty string WAS accepted as title")
    print(f"  env.title = {repr(env.title)}")
    
    # Check if validation catches it
    try:
        dict_result = env.to_dict()
        print("  to_dict() succeeded - validation PASSED empty string")
        print(f"  Resource type: {dict_result.get('Type')}")
        
        # This would be a bug since empty string doesn't match ^[a-zA-Z0-9]+$
        print("\nBUG FOUND: Empty string bypasses alphanumeric validation!")
        print("Expected: ValueError('Name \"\" not alphanumeric')")
        print("Actual: Empty string accepted")
        
    except ValueError as ve:
        print(f"  to_dict() raised ValueError: {ve}")
        if "not alphanumeric" in str(ve):
            print("  Validation caught empty string during to_dict()")
        
except ValueError as e:
    # This is the expected behavior
    print(f"RESULT: Empty string correctly REJECTED")
    print(f"  Error message: {e}")
    if "not alphanumeric" in str(e):
        print("  Correct error type (alphanumeric validation)")
        
except Exception as e:
    print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")

print("\n" + "="*50)
print("Test complete")