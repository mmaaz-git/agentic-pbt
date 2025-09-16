#!/usr/bin/env python3
"""Verify the negative application version bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.m2 as m2

# Test that negative application versions are accepted
deployment = m2.Deployment(
    title="TestDeploy",
    ApplicationId="app-123",
    ApplicationVersion=-42,  # Negative version doesn't make sense
    EnvironmentId="env-456"
)

# Serialize to see the output
result = deployment.to_dict()
print("Deployment with negative ApplicationVersion:")
print(result)

# The ApplicationVersion property uses the integer validator
# which only checks that the value can be converted to int,
# but doesn't enforce that it should be positive

# This is likely a bug - application versions should be positive integers