#!/usr/bin/env python3
"""Minimal reproduction of the None value bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.b2bi as b2bi

# Test 1: Setting optional property to None directly
print("Test 1: Setting optional Email property to None in Profile")
try:
    profile = b2bi.Profile(
        title="TestProfile",
        BusinessName="TestBusiness",
        Email=None,  # This is optional (False in props), should be allowed
        Logging="ENABLED",
        Name="TestName",
        Phone="123-456-7890"
    )
    print("✓ Success: Profile created with Email=None")
except TypeError as e:
    print(f"✗ BUG: {e}")

# Test 2: Let's check the props definition for Profile
print("\nTest 2: Checking Profile.props definition for Email")
print(f"Email prop definition: {b2bi.Profile.props.get('Email')}")

# Test 3: Setting optional property to None for other classes
print("\nTest 3: Testing S3Location with optional properties as None")
try:
    s3_loc = b2bi.S3Location(
        BucketName=None,  # Optional property
        Key=None  # Optional property
    )
    print("✓ Success: S3Location created with None values")
except TypeError as e:
    print(f"✗ BUG: {e}")

# Test 4: Not providing optional property at all
print("\nTest 4: Creating Profile without Email property")
try:
    profile2 = b2bi.Profile(
        title="TestProfile2",
        BusinessName="TestBusiness",
        # Email not provided at all
        Logging="ENABLED",
        Name="TestName",
        Phone="123-456-7890"
    )
    print("✓ Success: Profile created without Email property")
    print(f"  Email value: {getattr(profile2, 'Email', 'NOT SET')}")
except TypeError as e:
    print(f"✗ BUG: {e}")

# Test 5: Check if the issue affects all optional string properties
print("\nTest 5: Testing Partnership with optional Phone property as None")
try:
    partnership = b2bi.Partnership(
        title="TestPartnership",
        Capabilities=["capability1"],
        Email="test@example.com",
        Name="TestPartnership",
        Phone=None,  # Optional property
        ProfileId="profile-123"
    )
    print("✓ Success: Partnership created with Phone=None")
except TypeError as e:
    print(f"✗ BUG: {e}")

print("\n" + "="*60)
print("SUMMARY:")
print("The bug occurs when setting optional properties to None.")
print("Troposphere expects the correct type even for optional properties,")
print("and doesn't handle None values properly.")
print("This violates the common Python pattern where None indicates absence.")