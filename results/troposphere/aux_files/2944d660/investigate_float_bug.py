#!/usr/bin/env python3
"""Investigate the float bug in integer validator."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.kinesisvideo import SignalingChannel, Stream
from troposphere.validators import integer

# Test the integer validator directly
print("Testing integer validator directly:")
test_values = [1.1, 2.5, 3.9, -1.5]

for value in test_values:
    try:
        result = integer(value)
        print(f"  integer({value}) = {result!r} (type: {type(result).__name__})")
        print(f"    int({value}) = {int(value)}")
    except ValueError as e:
        print(f"  integer({value}) raised ValueError: {e}")

print("\nTesting with SignalingChannel:")
# Test with SignalingChannel
try:
    channel = SignalingChannel("Test", MessageTtlSeconds=1.1)
    print(f"  Created SignalingChannel with MessageTtlSeconds=1.1")
    print(f"  channel.MessageTtlSeconds = {channel.MessageTtlSeconds!r}")
    print(f"  Type: {type(channel.MessageTtlSeconds).__name__}")
except Exception as e:
    print(f"  Failed: {e}")

print("\nTesting with Stream:")
# Test with Stream
try:
    stream = Stream("Test", DataRetentionInHours=2.5)
    print(f"  Created Stream with DataRetentionInHours=2.5")
    print(f"  stream.DataRetentionInHours = {stream.DataRetentionInHours!r}")
    print(f"  Type: {type(stream.DataRetentionInHours).__name__}")
except Exception as e:
    print(f"  Failed: {e}")

print("\nChecking Python's int() behavior with floats:")
print(f"  int(1.1) = {int(1.1)}")
print(f"  int(2.5) = {int(2.5)}")
print(f"  int(3.9) = {int(3.9)}")
print(f"  int(-1.5) = {int(-1.5)}")