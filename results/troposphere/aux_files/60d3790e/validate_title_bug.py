#!/usr/bin/env python3
"""Reproduce title validation bug in troposphere.codeconnections"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codeconnections import Connection

print("Testing title validation bug in troposphere.codeconnections")
print("="*60)

# Test case 1: Invalid title with hyphens
print("\nTest 1: Creating Connection with invalid title containing hyphens")
print("Title: 'my-test-connection'")

try:
    # This title contains hyphens, which violates the alphanumeric requirement
    conn = Connection("my-test-connection", ConnectionName="TestConnection")
    
    # Try to convert to dict with validation enabled
    print("Calling to_dict(validation=True)...")
    result = conn.to_dict(validation=True)
    
    # If we get here, validation didn't catch the invalid title
    print("✗ BUG CONFIRMED: to_dict() accepted invalid title with hyphens")
    print(f"Output: {result}")
    
    # Now try explicit validation
    print("\nCalling validate_title() explicitly...")
    try:
        conn.validate_title()
        print("✗ SEVERE BUG: Even validate_title() accepted the invalid title!")
    except ValueError as e:
        print(f"✓ validate_title() correctly rejects it: {e}")
        print("\nThis confirms the bug: to_dict() doesn't call validate_title()")
        
except ValueError as e:
    print(f"✓ No bug - validation correctly rejected the title: {e}")
except Exception as e:
    print(f"? Unexpected error: {e}")

print("\n" + "="*60)

# Test case 2: Empty title
print("\nTest 2: Creating Connection with empty title")
print("Title: ''")

try:
    conn = Connection("", ConnectionName="TestConnection")
    
    print("Calling to_dict(validation=True)...")
    result = conn.to_dict(validation=True)
    
    print("✗ BUG CONFIRMED: to_dict() accepted empty title")
    print(f"Output keys: {result.keys()}")
    
    print("\nCalling validate_title() explicitly...")
    try:
        conn.validate_title()
        print("✗ SEVERE BUG: validate_title() accepted empty title!")
    except ValueError as e:
        print(f"✓ validate_title() correctly rejects it: {e}")
        
except ValueError as e:
    print(f"✓ No bug - validation correctly rejected: {e}")
except Exception as e:
    print(f"? Unexpected error: {e}")

print("\n" + "="*60)
print("CONCLUSION:")
print("If bugs were found above, the issue is that to_dict(validation=True)")
print("does not call validate_title() on the resource, allowing invalid")
print("CloudFormation resource names to be generated.")