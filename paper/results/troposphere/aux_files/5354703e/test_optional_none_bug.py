#!/usr/bin/env python3
"""Test if the None handling bug affects other optional properties"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import chatbot

print("Testing None handling for optional properties in troposphere.chatbot")
print("="*70)

# Test CustomActionAttachment optional properties
print("\n1. Testing CustomActionAttachment optional properties:")
failures = []

# ButtonText is optional
try:
    att1 = chatbot.CustomActionAttachment(ButtonText=None)
except TypeError as e:
    failures.append(("CustomActionAttachment.ButtonText", str(e)))
    print(f"   ✗ ButtonText=None failed: {e}")
else:
    print(f"   ✓ ButtonText=None succeeded")

# NotificationType is optional  
try:
    att2 = chatbot.CustomActionAttachment(NotificationType=None)
except TypeError as e:
    failures.append(("CustomActionAttachment.NotificationType", str(e)))
    print(f"   ✗ NotificationType=None failed: {e}")
else:
    print(f"   ✓ NotificationType=None succeeded")

# Variables is optional
try:
    att3 = chatbot.CustomActionAttachment(Variables=None)
except TypeError as e:
    failures.append(("CustomActionAttachment.Variables", str(e)))
    print(f"   ✗ Variables=None failed: {e}")
else:
    print(f"   ✓ Variables=None succeeded")

# Test CustomAction optional properties  
print("\n2. Testing CustomAction optional properties:")

# AliasName is optional
try:
    ca = chatbot.CustomAction("test")
    ca.ActionName = "test"
    ca.Definition = chatbot.CustomActionDefinition(CommandText="cmd")
    ca.AliasName = None
except TypeError as e:
    failures.append(("CustomAction.AliasName", str(e)))
    print(f"   ✗ AliasName=None failed: {e}")
else:
    print(f"   ✓ AliasName=None succeeded")

# Test SlackChannelConfiguration optional properties
print("\n3. Testing SlackChannelConfiguration optional properties:")

sc = chatbot.SlackChannelConfiguration("test")
sc.ConfigurationName = "test"
sc.IamRoleArn = "arn:test"
sc.SlackChannelId = "C123"
sc.SlackWorkspaceId = "T123"

# LoggingLevel is optional (but has validator)
try:
    sc2 = chatbot.SlackChannelConfiguration("test2")
    sc2.ConfigurationName = "test"
    sc2.IamRoleArn = "arn:test"
    sc2.SlackChannelId = "C123"
    sc2.SlackWorkspaceId = "T123"
    sc2.LoggingLevel = None
except (TypeError, ValueError) as e:
    failures.append(("SlackChannelConfiguration.LoggingLevel", str(e)))
    print(f"   ✗ LoggingLevel=None failed: {e}")
else:
    print(f"   ✓ LoggingLevel=None succeeded")

print("\n" + "="*70)
print(f"SUMMARY: Found {len(failures)} properties that incorrectly reject None:")
for prop, error in failures:
    print(f"  - {prop}")
    
if failures:
    print("\nThis is a systematic issue: optional properties should either")
    print("accept None or be omitted, but not reject None when explicitly set.")