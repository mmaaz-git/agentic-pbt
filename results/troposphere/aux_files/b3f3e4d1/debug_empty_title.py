#!/usr/bin/env python3
"""Debug empty title validation"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import launchwizard
import json

# Create deployment with empty title
deployment = launchwizard.Deployment(
    "",  # Empty title
    DeploymentPatternName="MyPattern",
    Name="MyDeployment",
    WorkloadName="MyWorkload"
)

print("Deployment created with empty title")
print(f"Title: {repr(deployment.title)}")
print(f"do_validation flag: {deployment.do_validation}")

print("\n1. Calling validate_title() directly:")
try:
    deployment.validate_title()
    print("  ✗ validate_title() passed (unexpected)")
except ValueError as e:
    print(f"  ✓ validate_title() failed: {e}")

print("\n2. Calling to_dict(validation=True):")
try:
    result = deployment.to_dict(validation=True)
    print("  ✓ to_dict(validation=True) succeeded")
    print(f"  Result keys: {result.keys()}")
    print(f"  Result: {json.dumps(result, indent=2)}")
except ValueError as e:
    print(f"  ✗ to_dict() failed: {e}")

print("\n3. Calling validate() method:")
try:
    deployment.validate()
    print("  ✓ validate() passed")
except Exception as e:
    print(f"  ✗ validate() failed: {e}")

print("\n4. Checking _validate_props():")
try:
    deployment._validate_props()
    print("  ✓ _validate_props() passed")
except ValueError as e:
    print(f"  ✗ _validate_props() failed: {e}")