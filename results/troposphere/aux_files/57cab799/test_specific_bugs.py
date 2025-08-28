#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.auditmanager import *
from troposphere.validators import double

print("=== Testing specific bugs ===")

# Test 1: The from_dict issue with Scope
print("\n1. Testing Scope.from_dict with nested structures")
scope1 = Scope(
    AwsAccounts=[
        AWSAccount(Id="123", Name="Test Account")
    ],
    AwsServices=[
        AWSService(ServiceName="S3")
    ]
)

dict_repr = scope1.to_dict()
print(f"Original dict: {dict_repr}")

# Try different ways to reconstruct
# Method 1: Direct from_dict (this is what should work per BaseAWSObject)
try:
    scope2 = Scope.from_dict(None, dict_repr)
    print("✓ from_dict with full dict works")
except Exception as e:
    print(f"✗ from_dict with full dict failed: {e}")

# Method 2: Using _from_dict with properties only
try:
    scope3 = Scope._from_dict(**dict_repr)
    print("✓ _from_dict with properties works")
except Exception as e:
    print(f"✗ _from_dict with properties failed: {e}")

# Test 2: Check if double accepts bytes that aren't valid numbers
print("\n2. Testing double with non-numeric bytes")
test_values = [
    b"hello",
    b"123abc",
    b"  123  ",  # with spaces
    b"",
    bytearray(b"world"),
    bytearray(b"456def"),
]

for val in test_values:
    double_ok = False
    float_ok = False
    
    try:
        double(val)
        double_ok = True
    except ValueError:
        pass
    
    try:
        float(val)
        float_ok = True
    except (ValueError, TypeError):
        pass
    
    if double_ok != float_ok:
        print(f"✗ INCONSISTENCY: double({val!r}) = {double_ok}, float({val!r}) = {float_ok}")
    else:
        print(f"✓ Consistent: double({val!r}) = {double_ok}, float({val!r}) = {float_ok}")

# Test 3: Special string values
print("\n3. Testing double with special strings")
special = ["Infinity", "-Infinity", "  inf  ", "  -inf  ", "  nan  "]
for s in special:
    double_ok = False
    float_ok = False
    
    try:
        double(s)
        double_ok = True
    except ValueError:
        pass
    
    try:
        float(s)
        float_ok = True
    except ValueError:
        pass
    
    if double_ok != float_ok:
        print(f"✗ INCONSISTENCY: double({s!r}) = {double_ok}, float({s!r}) = {float_ok}")
    else:
        print(f"✓ Consistent: double({s!r}) = {double_ok}, float({s!r}) = {float_ok}")