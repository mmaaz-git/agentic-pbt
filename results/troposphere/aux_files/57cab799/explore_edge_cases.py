#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.auditmanager import *
from troposphere.validators import double
import math

print("=== Testing double with edge cases ===")
# Test edge cases for double
edge_cases = [
    float('nan'),
    -float('inf'),
    1e308,  # Near max float
    1e-308, # Near min positive float
    sys.float_info.max,
    sys.float_info.min,
    "1e10",
    "inf",
    "-inf",
    "nan",
    "NaN",
    b"123",  # bytes
    bytearray(b"456"),  # bytearray
]

for val in edge_cases:
    try:
        result = double(val)
        print(f"double({repr(val)}) = {repr(result)} (type: {type(result).__name__})")
    except Exception as e:
        print(f"double({repr(val)}) raised: {e}")

print("\n=== Testing complex nested structures ===")
# Test nested properties
scope = Scope(
    AwsAccounts=[
        AWSAccount(Id="123456789", Name="Account1"),
        AWSAccount(Id="987654321", EmailAddress="test@example.com")
    ],
    AwsServices=[
        AWSService(ServiceName="S3"),
        AWSService(ServiceName="EC2")
    ]
)
scope_dict = scope.to_dict()
print(f"Scope dict: {scope_dict}")

# Can we reconstruct it?
try:
    scope2 = Scope.from_dict(None, **scope_dict)
    print(f"Reconstructed equals original? {scope.to_dict() == scope2.to_dict()}")
except Exception as e:
    print(f"Error reconstructing: {e}")

print("\n=== Testing property type validation ===")
# What happens if we pass wrong types?
test_cases = [
    ("Assessment", "Name", 123),  # int instead of str
    ("Assessment", "Roles", "not_a_list"),  # str instead of list
    ("Delegation", "CreationTime", []),  # list instead of double
    ("AWSAccount", "Id", None),  # None instead of str
]

for cls_name, prop, value in test_cases:
    cls = globals()[cls_name]
    try:
        obj = cls(**{prop: value})
        print(f"{cls_name}({prop}={repr(value)}) succeeded: {obj.to_dict()}")
    except Exception as e:
        print(f"{cls_name}({prop}={repr(value)}) raised: {type(e).__name__}: {e}")