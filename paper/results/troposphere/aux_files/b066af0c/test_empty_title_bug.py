#!/usr/bin/env python3
"""Test to demonstrate the empty title validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iot as iot
import troposphere

print("Demonstrating title validation bug in troposphere")
print("="*60)
print()

# The bug: Empty string and None titles bypass validation
print("BUG: Empty string and None titles bypass validation\n")

print("Expected behavior:")
print("  - All resource titles should be validated")
print("  - Empty strings and None should be rejected as invalid titles")
print("  - Only alphanumeric titles should be accepted")
print()

print("Actual behavior:")
print("  - Empty string titles are accepted without validation")
print("  - None titles are accepted without validation")
print("  - Non-empty titles are validated correctly")
print()

print("Demonstration:")
print("-" * 40)

# Test case 1: Empty string title
print("\n1. Creating Certificate with empty string title:")
try:
    cert = iot.Certificate(title="", Status="ACTIVE")
    print(f"   Result: ACCEPTED (title='{cert.title}')")
    print("   Expected: Should have raised ValueError")
    print("   ✗ BUG CONFIRMED: Empty title bypassed validation")
except ValueError as e:
    print(f"   Result: Rejected with error: {e}")
    print("   ✓ Worked as expected")

# Test case 2: None title  
print("\n2. Creating Certificate with None title:")
try:
    cert = iot.Certificate(title=None, Status="ACTIVE")
    print(f"   Result: ACCEPTED (title={cert.title})")
    print("   Expected: Should have raised ValueError")
    print("   ✗ BUG CONFIRMED: None title bypassed validation")
except (ValueError, AttributeError) as e:
    print(f"   Result: Rejected with error: {e}")
    print("   ✓ Worked as expected")

# Test case 3: Valid title (control)
print("\n3. Creating Certificate with valid title 'ValidCert123':")
try:
    cert = iot.Certificate(title="ValidCert123", Status="ACTIVE")
    print(f"   Result: ACCEPTED (title='{cert.title}')")
    print("   ✓ Worked as expected")
except ValueError as e:
    print(f"   Result: Rejected with error: {e}")
    print("   ✗ Unexpected rejection")

# Test case 4: Invalid title with special char (control)
print("\n4. Creating Certificate with invalid title 'Invalid-Title':")
try:
    cert = iot.Certificate(title="Invalid-Title", Status="ACTIVE")
    print(f"   Result: ACCEPTED (title='{cert.title}')")
    print("   ✗ Should have been rejected")
except ValueError as e:
    print(f"   Result: Rejected with error: {e}")
    print("   ✓ Worked as expected")

print("\n" + "="*60)
print("BUG SUMMARY:")
print("-" * 40)
print("The validate_title() method is only called when title is truthy.")
print("This allows empty strings and None to bypass validation entirely.")
print()
print("Root cause in __init__ method:")
print("  if self.title:")
print("      self.validate_title()")
print()
print("This should be:")
print("  self.validate_title()  # Always validate")
print()
print("Or the validate_title method should handle None gracefully.")

# Test that the bug affects all AWS resources, not just Certificate
print("\n" + "="*60)
print("Verifying bug affects all troposphere resources:")
print("-" * 40)

test_resources = [
    (iot.Thing, {"ThingName": "test"}),
    (iot.Policy, {"PolicyDocument": {}}),
    (iot.BillingGroup, {"BillingGroupName": "test"}),
]

for resource_class, props in test_resources:
    print(f"\nTesting {resource_class.__name__}:")
    try:
        obj = resource_class(title="", **props)
        print(f"  ✗ Empty title accepted for {resource_class.__name__}")
    except ValueError:
        print(f"  ✓ Empty title rejected for {resource_class.__name__}")