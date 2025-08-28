#!/usr/bin/env python3
"""Test if the boolean validator bug affects actual Grafana resources."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.grafana as grafana

# Test if PluginAdminEnabled property (which uses boolean validator) accepts floats
print("Testing Workspace.PluginAdminEnabled with float values:")

workspace = grafana.Workspace(
    title="TestWorkspace",
    AccountAccessType="CURRENT_ACCOUNT",
    AuthenticationProviders=["AWS_SSO"],
    PermissionType="SERVICE_MANAGED",
    PluginAdminEnabled=1.0  # Should be boolean, but float is accepted
)

# Convert to dict to see the result
workspace_dict = workspace.to_dict()
print(f"PluginAdminEnabled=1.0 -> {workspace_dict['Properties'].get('PluginAdminEnabled')}")

workspace2 = grafana.Workspace(
    title="TestWorkspace2",
    AccountAccessType="CURRENT_ACCOUNT",
    AuthenticationProviders=["AWS_SSO"],
    PermissionType="SERVICE_MANAGED",
    PluginAdminEnabled=0.0  # Should be boolean, but float is accepted
)

workspace2_dict = workspace2.to_dict()
print(f"PluginAdminEnabled=0.0 -> {workspace2_dict['Properties'].get('PluginAdminEnabled')}")

# This affects CloudFormation template generation
print("\nGenerated CloudFormation JSON:")
print(workspace.to_json(indent=2))