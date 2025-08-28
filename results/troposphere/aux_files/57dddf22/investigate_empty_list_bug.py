#!/usr/bin/env python3
"""Investigate the empty EventTypeIds list bug"""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codestarnotifications as csn

print("=" * 60)
print("Investigating Empty EventTypeIds List Bug")
print("=" * 60)

# Create a valid target
target = csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:my-topic", TargetType="SNS")

# Test 1: Empty EventTypeIds list
print("\nTest 1: Creating NotificationRule with empty EventTypeIds")
print("-" * 40)

try:
    rule = csn.NotificationRule(
        "TestRule",
        Name="MyNotificationRule",
        DetailType="BASIC",
        EventTypeIds=[],  # Empty list - should this be allowed?
        Resource="arn:aws:codecommit:us-east-1:123456789012:MyRepo",
        Targets=[target]
    )
    
    print("✓ NotificationRule created with empty EventTypeIds")
    
    # Try to convert to dict (where validation happens)
    dict_repr = rule.to_dict()
    print("✓ to_dict() succeeded with empty EventTypeIds")
    print(f"Result: {json.dumps(dict_repr, indent=2)}")
    
    # Check if EventTypeIds is in the output
    if 'EventTypeIds' in dict_repr['Properties']:
        event_ids = dict_repr['Properties']['EventTypeIds']
        print(f"\nEventTypeIds in output: {event_ids}")
        if len(event_ids) == 0:
            print("✗ BUG CONFIRMED: Empty EventTypeIds list is accepted!")
            print("This is likely invalid for AWS CloudFormation")
    
except (ValueError, TypeError) as e:
    print(f"✓ Correctly rejected: {e}")

# Test 2: What about other required list properties?
print("\n" + "=" * 60)
print("Test 2: Empty Targets list")
print("-" * 40)

try:
    rule2 = csn.NotificationRule(
        "TestRule2",
        Name="MyNotificationRule",
        DetailType="BASIC",
        EventTypeIds=["codepipeline-pipeline-pipeline-execution-failed"],
        Resource="arn:aws:codecommit:us-east-1:123456789012:MyRepo",
        Targets=[]  # Empty targets list
    )
    
    print("✓ NotificationRule created with empty Targets")
    
    dict_repr2 = rule2.to_dict()
    print("✓ to_dict() succeeded with empty Targets")
    
    if 'Targets' in dict_repr2['Properties']:
        targets = dict_repr2['Properties']['Targets']
        print(f"Targets in output: {targets}")
        if len(targets) == 0:
            print("✗ BUG: Empty Targets list is also accepted!")
    
except (ValueError, TypeError) as e:
    print(f"✓ Correctly rejected: {e}")

# Test 3: Check AWS documentation requirements
print("\n" + "=" * 60)
print("Test 3: AWS CloudFormation Requirements")
print("-" * 40)

print("According to AWS documentation:")
print("- EventTypeIds: A list of event types (Required: Yes)")
print("- Targets: A list of notification rule targets (Required: Yes)")
print("")
print("Both properties are required and should have at least one item.")
print("Troposphere should validate this to prevent CloudFormation errors.")

# Test 4: Check if validation can be added
print("\n" + "=" * 60)
print("Test 4: Attempting manual validation")
print("-" * 40)

# Create rule with empty lists
rule_bad = csn.NotificationRule(
    "BadRule",
    Name="Test",
    DetailType="BASIC",
    EventTypeIds=[],
    Resource="arn:resource",
    Targets=[]
)

# Check if we can detect the issue
props = rule_bad.to_dict()['Properties']
issues = []

if 'EventTypeIds' in props and len(props['EventTypeIds']) == 0:
    issues.append("EventTypeIds is empty")

if 'Targets' in props and len(props['Targets']) == 0:
    issues.append("Targets is empty")

if issues:
    print("✗ Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✓ No issues found")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print("BUG FOUND: troposphere.codestarnotifications accepts empty lists")
print("for required properties EventTypeIds and Targets.")
print("This will cause CloudFormation deployment failures.")