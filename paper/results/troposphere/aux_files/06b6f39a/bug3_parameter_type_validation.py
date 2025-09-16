#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""
Bug 3: Parameter type validation is too permissive for defaults
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Parameter

print("Testing Parameter type validation for default values...")

# Test 1: String type with integer default
print("\n--- String type with integer default ---")
try:
    param1 = Parameter("StringParam", Type="String", Default=123)
    param1.validate()
    print(f"✗ BUG: String parameter accepts integer default: {param1.properties.get('Default')}")
    print(f"  This violates CloudFormation spec: String params need string defaults")
except (ValueError, TypeError) as e:
    print(f"✓ Correctly rejected: {e}")

# Test 2: String type with float default
print("\n--- String type with float default ---")
try:
    param2 = Parameter("StringParam2", Type="String", Default=3.14)
    param2.validate()
    print(f"✗ BUG: String parameter accepts float default: {param2.properties.get('Default')}")
except (ValueError, TypeError) as e:
    print(f"✓ Correctly rejected: {e}")

# Test 3: Number type with empty string default
print("\n--- Number type with empty string default ---")
try:
    param3 = Parameter("NumberParam", Type="Number", Default="")
    param3.validate()
    print(f"✗ BUG: Number parameter accepts empty string default: {param3.properties.get('Default')}")
    print(f"  Empty string is not a valid number!")
except (ValueError, TypeError) as e:
    print(f"✓ Correctly rejected: {e}")

# Test 4: Number type with non-numeric string
print("\n--- Number type with non-numeric string ---")
try:
    param4 = Parameter("NumberParam2", Type="Number", Default="abc")
    param4.validate()
    print(f"✗ BUG: Number parameter accepts non-numeric string: {param4.properties.get('Default')}")
except (ValueError, TypeError) as e:
    print(f"✓ Correctly rejected: {e}")

# Test 5: Valid cases that should work
print("\n--- Valid cases ---")
try:
    param5 = Parameter("ValidString", Type="String", Default="test")
    param5.validate()
    print(f"✓ String with string default works")
except Exception as e:
    print(f"✗ Unexpectedly failed: {e}")

try:
    param6 = Parameter("ValidNumber", Type="Number", Default=42)
    param6.validate()
    print(f"✓ Number with integer default works")
except Exception as e:
    print(f"✗ Unexpectedly failed: {e}")

try:
    param7 = Parameter("ValidNumber2", Type="Number", Default="42")
    param7.validate()
    print(f"✓ Number with numeric string default works")
except Exception as e:
    print(f"✗ Unexpectedly failed: {e}")