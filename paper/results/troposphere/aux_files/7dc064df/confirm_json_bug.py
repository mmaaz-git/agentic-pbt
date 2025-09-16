#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.connectcampaigns as cc
import json

print("Testing if troposphere generates valid JSON for special float values\n")

test_cases = [
    ("NaN", float('nan')),
    ("Infinity", float('inf')),
    ("-Infinity", float('-inf'))
]

for name, value in test_cases:
    print(f"Testing {name}:")
    config = cc.AgentlessDialerConfig(DialingCapacity=value)
    
    # Get the JSON string
    json_str = config.to_json()
    print(f"  Generated JSON: {json_str[:50]}...")
    
    # Try to parse with standard json.loads (strict mode)
    try:
        # Standard JSON doesn't support NaN/Infinity
        # This should fail if the JSON is invalid
        import json as std_json
        parsed = std_json.loads(json_str, strict=True)
        print(f"  ✓ Successfully parsed with strict JSON parser")
    except ValueError as e:
        print(f"  ✗ Invalid JSON: {e}")
    
    print()

# Test that this affects real Campaign objects too
print("Testing with full Campaign object:")
campaign = cc.Campaign(
    "TestCampaign",
    ConnectInstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
    DialerConfig=cc.DialerConfig(
        AgentlessDialerConfig=cc.AgentlessDialerConfig(DialingCapacity=float('nan'))
    ),
    Name="TestCampaign",
    OutboundCallConfig=cc.OutboundCallConfig(
        ConnectContactFlowArn="arn:aws:connect:us-east-1:123456789012:instance/test/flow/test"
    )
)

json_str = campaign.to_json()
print(f"Campaign JSON snippet: ...{json_str[200:400]}...")

try:
    import json as std_json
    parsed = std_json.loads(json_str, strict=True)
    print("✓ Valid JSON")
except ValueError as e:
    print(f"✗ Invalid JSON: {e}")

# Check if this would be a problem for AWS CloudFormation
print("\nNote: AWS CloudFormation templates must be valid JSON or YAML.")
print("Invalid JSON with NaN/Infinity would cause deployment failures.")