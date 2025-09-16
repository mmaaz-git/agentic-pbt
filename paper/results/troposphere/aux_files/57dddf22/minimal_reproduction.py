#!/usr/bin/env python3
"""Minimal reproduction of empty list validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codestarnotifications as csn

# Create NotificationRule with empty EventTypeIds
rule = csn.NotificationRule(
    "MyRule",
    Name="TestNotification",
    DetailType="BASIC",
    EventTypeIds=[],  # Empty list - should be rejected
    Resource="arn:aws:codecommit:us-east-1:123456789012:MyRepo",
    Targets=[csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:topic", TargetType="SNS")]
)

# Generate CloudFormation template
template = rule.to_dict()
print("Generated template with empty EventTypeIds:")
print(template)

# This will fail when deployed to CloudFormation with:
# "Property validation failure: [The property EventTypeIds must have at least 1 element(s)]"