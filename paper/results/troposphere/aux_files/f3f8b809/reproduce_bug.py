#!/usr/bin/env python3
"""Minimal reproduction of the title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.lookoutequipment as le

# This character is considered alphanumeric by Python
char = 'µ'
print(f"Is '{char}' alphanumeric according to Python? {char.isalnum()}")

# But it fails the troposphere title validation
try:
    config = le.S3InputConfiguration(
        title=char,
        Bucket='test-bucket'
    )
    print("Title validation passed")
except ValueError as e:
    print(f"Title validation failed: {e}")

# Another example with a different Unicode letter
char2 = 'π'
print(f"\nIs '{char2}' alphanumeric according to Python? {char2.isalnum()}")

try:
    config = le.S3InputConfiguration(
        title=char2,
        Bucket='test-bucket'
    )
    print("Title validation passed")
except ValueError as e:
    print(f"Title validation failed: {e}")