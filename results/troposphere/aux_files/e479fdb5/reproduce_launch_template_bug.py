#!/usr/bin/env python3
"""Minimal reproduction of LaunchTemplateSpecification validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.autoscaling import LaunchTemplateSpecification

# Test 1: Valid with LaunchTemplateId and Version
print("Test 1: LaunchTemplateId + Version (should work)")
try:
    spec = LaunchTemplateSpecification(LaunchTemplateId="lt-123", Version="1")
    spec.validate()
    print("Success: Created with LaunchTemplateId and Version")
except Exception as e:
    print(f"Failed: {e}")

# Test 2: Valid with LaunchTemplateName and Version  
print("\nTest 2: LaunchTemplateName + Version (should work)")
try:
    spec = LaunchTemplateSpecification(LaunchTemplateName="my-template", Version="1")
    spec.validate()
    print("Success: Created with LaunchTemplateName and Version")
except Exception as e:
    print(f"Failed: {e}")

# Test 3: Invalid with both ID and Name
print("\nTest 3: Both LaunchTemplateId and LaunchTemplateName (should fail)")
try:
    spec = LaunchTemplateSpecification(
        LaunchTemplateId="lt-123",
        LaunchTemplateName="my-template", 
        Version="1"
    )
    spec.validate()
    print("BUG: Should have failed with both ID and Name")
except ValueError as e:
    print(f"Correctly failed: {e}")

# Test 4: Invalid with only Version (no ID or Name)
print("\nTest 4: Only Version without ID or Name (should fail)")
try:
    spec = LaunchTemplateSpecification(Version="1")
    spec.validate()
    print("BUG: Should have failed with only Version")
except ValueError as e:
    print(f"Correctly failed: {e}")