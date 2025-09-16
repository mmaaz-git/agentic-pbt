#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import troposphere.connectcampaigns as cc
from troposphere import Template

print("Demonstrating real-world impact of NaN/Infinity bug\n")

# Create a CloudFormation template
template = Template()
template.set_description("Test template for AWS Connect Campaign")

# Add a campaign with NaN value
campaign = cc.Campaign(
    "MyConnectCampaign",
    ConnectInstanceArn="arn:aws:connect:us-east-1:123456789012:instance/abc123",
    DialerConfig=cc.DialerConfig(
        AgentlessDialerConfig=cc.AgentlessDialerConfig(
            DialingCapacity=float('nan')  # This could happen from calculations
        )
    ),
    Name="ProductionCampaign",
    OutboundCallConfig=cc.OutboundCallConfig(
        ConnectContactFlowArn="arn:aws:connect:us-east-1:123456789012:instance/abc123/flow/def456"
    )
)

template.add_resource(campaign)

# Generate the "CloudFormation template"
cf_json = template.to_json()

print("Generated CloudFormation template (first 500 chars):")
print(cf_json[:500])
print("...")

# Try to validate as strict JSON (as AWS would)
print("\nValidation as CloudFormation would do it:")
try:
    parsed = json.loads(cf_json, allow_nan=False)
    print("✓ Template is valid JSON")
except ValueError as e:
    print(f"✗ Template contains invalid JSON: {e}")
    print("\nThis template would be REJECTED by AWS CloudFormation!")
    print("Error: CloudFormation requires valid JSON or YAML.")
    
print("\nHow this bug could occur in practice:")
print("1. User performs calculation that results in NaN (e.g., 0.0/0.0)")
print("2. User sets this as DialingCapacity without realizing it's NaN")
print("3. troposphere accepts it without validation")
print("4. to_json() generates invalid JSON")
print("5. AWS CloudFormation deployment fails with cryptic error")
print("\nThe bug violates the library's contract to generate valid CloudFormation templates.")