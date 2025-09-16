#!/usr/bin/env python3
"""Minimal reproduction of integer validator bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.networkfirewall import PortRange

# Test 1: Float values are accepted but stored as floats
port_range = PortRange(FromPort=80.0, ToPort=443.5)
print(f"FromPort value: {port_range.properties['FromPort']}")
print(f"FromPort type: {type(port_range.properties['FromPort'])}")
print(f"ToPort value: {port_range.properties['ToPort']}")
print(f"ToPort type: {type(port_range.properties['ToPort'])}")

# Test 2: The to_dict() output contains floats, not integers
result = port_range.to_dict()
print(f"\nto_dict() result: {result}")
print(f"FromPort in dict: {result['FromPort']} (type: {type(result['FromPort'])})")
print(f"ToPort in dict: {result['ToPort']} (type: {type(result['ToPort'])})")

# Test 3: Direct test of the integer validator
from troposphere.validators import integer

test_values = [1, 1.0, 1.5, 2.9]
for val in test_values:
    result = integer(val)
    print(f"\ninteger({val}) returns: {result} (type: {type(result)})")
    print(f"  Expected: integer type, Got: {type(result).__name__}")