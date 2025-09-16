#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("Bug 1: validate_authorizer_ttl accepts 0 but shouldn't")
print("=" * 60)
from troposphere.validators.apigatewayv2 import validate_authorizer_ttl

try:
    result = validate_authorizer_ttl(0)
    print(f"✗ validate_authorizer_ttl(0) returned {result} - expected to fail")
    print(f"  This allows TTL of 0 seconds, which is likely not intended")
    print()
except ValueError as e:
    print(f"✓ validate_authorizer_ttl(0) correctly raised: {e}")
    print()

print("Bug 2: Title validation accepts empty string")
print("=" * 60)
from troposphere import BaseAWSObject

class TestResource(BaseAWSObject):
    resource_type = "Test::Resource"
    props = {}

try:
    obj = TestResource(title="", validation=True)
    print(f"✗ Creating resource with empty title succeeded - expected to fail")
    print(f"  Empty resource names are likely not valid in CloudFormation")
    print()
except ValueError as e:
    print(f"✓ Empty title correctly raised: {e}")
    print()

print("Bug 3: validation=False doesn't skip title validation")  
print("=" * 60)

try:
    # Using a clearly invalid title with validation=False
    obj = TestResource(title="test-with-dashes", validation=False)
    print(f"✗ validation=False still validates title - expected to skip validation")
    print(f"  This defeats the purpose of the validation=False flag")
    print()
except ValueError as e:
    print(f"✗ validation=False raised error anyway: {e}")
    print(f"  The validation=False flag is ignored for title validation")
    print()

print("Bug 4: Unicode vs ASCII alphanumeric mismatch")
print("=" * 60)

# Test with superscript 1 (¹) which is alphanumeric in Unicode but not ASCII
unicode_char = "¹"
print(f"Testing with Unicode character: '{unicode_char}'")
print(f"Python isalnum(): {unicode_char.isalnum()}")

import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
print(f"Regex match: {bool(valid_names.match(unicode_char))}")

try:
    obj = TestResource(title=unicode_char, validation=True)
    print(f"✗ Unicode alphanumeric character accepted as title")
except ValueError as e:
    print(f"✓ Unicode character correctly rejected: {e}")
    
print()
print("This shows inconsistency between isalnum() check and regex validation")