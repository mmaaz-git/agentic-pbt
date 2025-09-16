#!/usr/bin/env python3
"""Investigate the test failures to determine if they are genuine bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
import troposphere
from troposphere import Template, Parameter, AWSObject

print("=== Investigating Test Failures ===\n")

# Failure 1: Parameter title accepts empty string
print("1. Parameter title validation with empty string:")
print("-" * 50)
try:
    param = Parameter("", Type="String")
    print(f"✗ BUG: Empty string accepted as title!")
    print(f"  Created parameter with title: {param.title!r}")
    print(f"  Pattern should require: ^[a-zA-Z0-9]+$ (+ means one or more)")
    print(f"  Pattern used: {troposphere.valid_names.pattern}")
except ValueError as e:
    print(f"✓ Empty string correctly rejected: {e}")

print("\n2. Parameter title validation - checking the regex:")
print("-" * 50)
print(f"Pattern: {troposphere.valid_names.pattern}")
print(f"Testing empty string: {troposphere.valid_names.match('')}")
print(f"Testing 'A': {troposphere.valid_names.match('A')}")
print(f"Testing 'Test123': {troposphere.valid_names.match('Test123')}")

# Failure 2: Parameter String type accepts integer Default
print("\n3. Parameter String type with integer Default:")
print("-" * 50)
try:
    param = Parameter("TestParam", Type="String", Default=0)
    print(f"✗ Parameter created with integer default for String type")
    print(f"  Default value: {param.Default!r} (type: {type(param.Default)})")
    
    # Now try to validate it
    print("  Calling validate()...")
    param.validate()
    print(f"✗ BUG: Validation passed! Integer accepted as Default for String type")
except (ValueError, TypeError) as e:
    print(f"✓ Integer default correctly rejected: {e}")

# Let's also test with other non-string types
print("\n4. Testing other non-string defaults for String type:")
print("-" * 50)
test_values = [
    (42, "integer"),
    (3.14, "float"),
    (True, "boolean"),
    (False, "boolean"),
    ([], "list"),
    ({}, "dict"),
]

for value, type_name in test_values:
    try:
        param = Parameter(f"Test{type_name}", Type="String", Default=value)
        param.validate()
        print(f"✗ BUG: {type_name} value {value!r} accepted as Default for String type")
    except (ValueError, TypeError) as e:
        print(f"✓ {type_name} correctly rejected: {str(e)[:80]}...")

# Failure 3: AWSObject resource_type
print("\n5. AWSObject resource_type attribute:")
print("-" * 50)
try:
    resource = AWSObject("TestResource")
    print(f"Created AWSObject: {resource}")
    print(f"Checking if resource_type exists: {hasattr(resource, 'resource_type')}")
    
    # Try to set it
    resource.resource_type = "AWS::CloudFormation::WaitConditionHandle"
    print(f"✓ Successfully set resource_type")
except AttributeError as e:
    print(f"✗ Cannot set resource_type: {e}")
    print("  This is expected - AWSObject subclasses define resource_type as class attribute")
    
# Let's check how to properly create resources
print("\n6. Proper way to create resources:")
print("-" * 50)
print("Looking at ec2.Instance as an example...")
from troposphere import ec2
instance = ec2.Instance("MyInstance")
print(f"Instance created: {instance}")
print(f"Instance resource_type: {instance.resource_type}")
print(f"Instance title: {instance.title}")

# Check template resource addition
template = Template()
template.add_resource(instance)
print(f"Successfully added to template. Resources count: {len(template.resources)}")