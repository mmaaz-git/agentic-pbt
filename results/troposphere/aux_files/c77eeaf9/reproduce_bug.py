#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import AWSProperty, AWSObject

print("Bug Reproduction: Property Name Conflicts with Internal Attributes")
print("="*70)

# Demonstrate the bug with a minimal example
class UserDefinedProperty(AWSProperty):
    """A property class where user wants to have a 'template' field"""
    props = {
        'template': (str, True),  # User wants a required field called 'template'
        'normal_field': (str, True)  # A normal field for comparison
    }

print("\nScenario: User defines a CloudFormation property with a 'template' field")
print("-"*70)

# Create instance and set both fields
obj = UserDefinedProperty()
obj.template = "my_template_value"
obj.normal_field = "my_normal_value"

print(f"Set obj.template = 'my_template_value'")
print(f"Set obj.normal_field = 'my_normal_value'")
print()

# Check what actually happened
print("Checking internal state:")
print(f"  obj.template (internal attribute) = {obj.template}")
print(f"  obj.normal_field = {obj.normal_field}")
print(f"  obj.properties dict = {obj.properties}")
print()

# The bug: 'template' is NOT in properties dict!
print("BUG DEMONSTRATED:")
print(f"  'template' in obj.properties: {'template' in obj.properties}")
print(f"  'normal_field' in obj.properties: {'normal_field' in obj.properties}")
print()

# This causes validation to fail
print("Attempting to validate (will fail):")
try:
    result = obj.to_dict(validation=True)
    print(f"  Success: {result}")
except ValueError as e:
    print(f"  Error: {e}")
    print()
    print("  Even though we set obj.template, it was stored as an internal")
    print("  attribute instead of a property, so validation fails!")

print("\n" + "="*70)
print("Additional test: 'properties' field name")
print("-"*70)

class AnotherProblematicProperty(AWSProperty):
    props = {
        'properties': (str, True)
    }

try:
    obj2 = AnotherProblematicProperty()
    obj2.properties = "test"
    print(f"Set obj2.properties = 'test'")
    print(f"Type of obj2.properties after setting: {type(obj2.properties)}")
    print("BUG: Setting 'properties' overwrites the internal dict!")
    result = obj2.to_dict(validation=True)
except Exception as e:
    print(f"Error: {e}")
    print("The internal properties dict was replaced with a string!")

print("\n" + "="*70)
print("SUMMARY:")
print("-"*70)
print("This is a CONTRACT VIOLATION bug where:")
print("1. The API allows users to define properties with any name")
print("2. But certain names conflict with internal BaseAWSObject attributes")
print("3. This causes silent data corruption or unexpected validation failures")
print("4. The behavior violates the principle of least surprise")
print()
print("Affected internal attributes include:")
print("  - template, title, properties, resource, attributes, do_validation, etc.")
print()
print("Impact: Users creating CloudFormation templates with these field names")
print("will experience mysterious failures and data loss.")