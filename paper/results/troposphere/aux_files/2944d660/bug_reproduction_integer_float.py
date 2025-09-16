#!/usr/bin/env python3
"""Bug reproduction: integer validator accepts non-integer floats."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.kinesisvideo import SignalingChannel, Stream
from troposphere.validators import integer

# Demonstrate the bug
print("BUG: The 'integer' validator accepts non-integer float values")
print("=" * 60)

# Test 1: integer validator accepts floats with fractional parts
print("\n1. integer() validator accepts floats with fractional parts:")
test_floats = [1.1, 2.5, 3.9, -1.5, 100.999]
for f in test_floats:
    result = integer(f)
    print(f"   integer({f}) = {result} (type: {type(result).__name__})")
    print(f"      This silently truncates to {int(f)} when converted")

# Test 2: This allows invalid values in AWS resources
print("\n2. AWS resources accept non-integer values for integer properties:")
channel = SignalingChannel("TestChannel", MessageTtlSeconds=300.7)
print(f"   SignalingChannel created with MessageTtlSeconds=300.7")
print(f"   Actual value stored: {channel.MessageTtlSeconds}")

stream = Stream("TestStream", DataRetentionInHours=24.999)
print(f"   Stream created with DataRetentionInHours=24.999")
print(f"   Actual value stored: {stream.DataRetentionInHours}")

# Test 3: This could cause issues in CloudFormation
print("\n3. CloudFormation template with non-integer values:")
channel_dict = channel.to_dict()
print(f"   SignalingChannel.to_dict() produces:")
print(f"   {channel_dict['Properties']}")

print("\nExpected behavior: The integer validator should reject float values")
print("with fractional parts, raising a ValueError.")