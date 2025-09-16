#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.pcaconnectorad import EnrollmentFlagsV2, PrivateKeyAttributesV2
from troposphere.validators import boolean, double

print("=== Test 1: Setting boolean property after creation ===")
flags = EnrollmentFlagsV2()
print(f"Initial properties: {flags.properties}")

# Try setting with various boolean representations
test_values = [
    ("true", "string 'true'"),
    ("True", "string 'True'"),
    (1, "integer 1"),
    (True, "boolean True"),
    ("yes", "string 'yes'"),  # Should fail
]

for value, description in test_values:
    try:
        flags.UserInteractionRequired = value
        print(f"✓ Set UserInteractionRequired to {description}: {flags.properties.get('UserInteractionRequired')}")
    except Exception as e:
        print(f"✗ Failed to set UserInteractionRequired to {description}: {e}")

print("\n=== Test 2: Setting double property after creation ===")
pka = PrivateKeyAttributesV2(KeySpec="RSA", MinimalKeyLength=2048)
print(f"Initial MinimalKeyLength: {pka.properties.get('MinimalKeyLength')}")

# Try setting with various numeric representations
test_values = [
    (4096, "integer 4096"),
    ("8192", "string '8192'"),
    (1024.5, "float 1024.5"),
    ("not_a_number", "string 'not_a_number'"),  # Should fail
]

for value, description in test_values:
    try:
        pka.MinimalKeyLength = value
        print(f"✓ Set MinimalKeyLength to {description}: {pka.properties.get('MinimalKeyLength')}")
    except Exception as e:
        print(f"✗ Failed to set MinimalKeyLength to {description}: {e}")

print("\n=== Test 3: Testing validator function behavior directly ===")
# The boolean validator claims to accept "1" but what about 1.0?
test_cases = [
    (1.0, "float 1.0"),
    (0.0, "float 0.0"),
    (1.5, "float 1.5"),
]

for value, description in test_cases:
    try:
        result = boolean(value)
        print(f"boolean({description}) = {result}")
    except ValueError:
        print(f"boolean({description}) raised ValueError")

print("\n=== Test 4: Testing with complex boolean representations ===")
# What if we pass something that evaluates to True/False in Python but isn't in the list?
test_cases = [
    ([], "empty list"),
    ([1], "non-empty list"),
    ("", "empty string"),
    ("anything", "non-empty string"),
    (None, "None"),
    ({}, "empty dict"),
    ({"a": 1}, "non-empty dict"),
]

for value, description in test_cases:
    try:
        result = boolean(value)
        print(f"boolean({description}) = {result} - UNEXPECTED SUCCESS")
    except (ValueError, TypeError) as e:
        print(f"boolean({description}) raised {type(e).__name__}")