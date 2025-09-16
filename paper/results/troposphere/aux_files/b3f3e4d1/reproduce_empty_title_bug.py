#!/usr/bin/env python3
"""Minimal reproduction of the empty title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import launchwizard

# Bug: Empty title passes initialization but fails validation
deployment = launchwizard.Deployment(
    "",  # Empty title - should fail but doesn't during init
    DeploymentPatternName="MyPattern",
    Name="MyDeployment",
    WorkloadName="MyWorkload"
)

print("✓ Deployment created with empty title (no error during __init__)")
print(f"  Title value: {repr(deployment.title)}")

# But it fails when we try to validate or convert to dict
try:
    deployment.to_dict(validation=True)
    print("✗ to_dict() succeeded (unexpected)")
except ValueError as e:
    print(f"✗ to_dict() failed with: {e}")
    print("  This shows the inconsistency - init accepts it, but validation rejects it")