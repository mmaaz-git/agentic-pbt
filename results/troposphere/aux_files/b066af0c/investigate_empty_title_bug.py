#!/usr/bin/env python3
"""Investigate the empty title bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iot as iot
import troposphere
import re

print("Investigating empty title bug in troposphere...")
print(f"Troposphere version: {troposphere.__version__}")
print()

# Check the validation regex
print("Title validation regex pattern:")
print(f"  Pattern: {troposphere.valid_names.pattern}")
print(f"  Regex object: {troposphere.valid_names}")
print()

# Test the regex directly
test_cases = [
    "",           # Empty string
    " ",          # Space
    "ABC",        # Valid
    "123",        # Valid numbers
    "Test123",    # Valid alphanumeric
    "Test_123",   # With underscore
    "Test-123",   # With hyphen
]

print("Testing regex directly:")
for test in test_cases:
    match = troposphere.valid_names.match(test)
    print(f"  '{test}': {'matches' if match else 'no match'}")
print()

# Test Certificate creation with various titles
print("Testing Certificate creation:")
for test in test_cases:
    try:
        cert = iot.Certificate(title=test, Status="ACTIVE")
        print(f"  '{test}': ✓ Accepted (title={cert.title})")
    except ValueError as e:
        print(f"  '{test}': ✗ Rejected ({e})")
print()

# Test with None title
print("Testing None title:")
try:
    cert = iot.Certificate(title=None, Status="ACTIVE")
    print(f"  None: ✓ Accepted (title={cert.title})")
except (ValueError, AttributeError) as e:
    print(f"  None: ✗ Rejected ({e})")
print()

# Check the actual validation logic
print("Checking validation logic in BaseAWSObject:")
print(f"  BaseAWSObject.validate_title method exists: {hasattr(troposphere.BaseAWSObject, 'validate_title')}")

# Let's check if validation is actually called
print("\nChecking when validate_title is called:")
class TestObject(troposphere.AWSObject):
    resource_type = "Test::Resource"
    props = {"Status": (str, True)}
    
    def validate_title(self):
        print(f"    validate_title called with title='{self.title}'")
        super().validate_title()

try:
    print("  Creating with empty title:")
    obj = TestObject(title="", Status="test")
except ValueError as e:
    print(f"    Raised: {e}")

try:
    print("  Creating with None title:")
    obj = TestObject(title=None, Status="test")
except (ValueError, AttributeError) as e:
    print(f"    Raised: {e}")

try:
    print("  Creating with valid title:")
    obj = TestObject(title="Valid123", Status="test")
except ValueError as e:
    print(f"    Raised: {e}")

# Check the actual source of validate_title
print("\nExamining validate_title source:")
import inspect
source = inspect.getsource(troposphere.BaseAWSObject.validate_title)
print(source)