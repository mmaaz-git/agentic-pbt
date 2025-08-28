#!/usr/bin/env python3
"""Verify the Tags handling issue"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import launchwizard, Tags

print("Testing Tags parameter handling")
print("-" * 50)

# Test 1: Can we pass None for optional Tags?
print("\n1. Testing Tags=None (should this work for optional param?)")
try:
    deployment = launchwizard.Deployment(
        "Test1",
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload",
        Tags=None
    )
    print("✓ Tags=None accepted")
except TypeError as e:
    print(f"✗ Tags=None rejected: {e}")

# Test 2: What about not passing Tags at all?
print("\n2. Testing without Tags parameter (omitted)")
try:
    deployment = launchwizard.Deployment(
        "Test2",
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload"
        # No Tags parameter
    )
    print("✓ Omitting Tags works")
    print(f"  Has Tags attr? {hasattr(deployment, 'Tags')}")
    if hasattr(deployment, 'Tags'):
        print(f"  Tags value: {getattr(deployment, 'Tags', 'N/A')}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Empty Tags object
print("\n3. Testing Tags=Tags() (empty Tags object)")
try:
    deployment = launchwizard.Deployment(
        "Test3",
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload",
        Tags=Tags()
    )
    print("✓ Tags() accepted")
    deployment_dict = deployment.to_dict()
    print(f"  Tags in dict: {deployment_dict.get('Properties', {}).get('Tags')}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Tags with empty dict
print("\n4. Testing Tags=Tags(**{}) (Tags from empty dict)")
empty_dict = {}
try:
    deployment = launchwizard.Deployment(
        "Test4",
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload",
        Tags=Tags(**empty_dict)
    )
    print("✓ Tags(**{}) accepted")
    deployment_dict = deployment.to_dict()
    print(f"  Tags in dict: {deployment_dict.get('Properties', {}).get('Tags')}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 50)
print("Property definition analysis:")
print("-" * 50)

# Check the property definition
print(f"Tags property definition: {launchwizard.Deployment.props['Tags']}")
print(f"  Type: {launchwizard.Deployment.props['Tags'][0]}")
print(f"  Required: {launchwizard.Deployment.props['Tags'][1]}")

print("\nConclusion: Tags is optional (False) but when provided must be a Tags object, not None")