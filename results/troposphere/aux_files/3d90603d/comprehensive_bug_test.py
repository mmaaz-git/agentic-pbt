#!/usr/bin/env python3
"""
Comprehensive test demonstrating the title validation bug in Troposphere
"""
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.pcaconnectorscep as pcaconnectorscep
import json

print("=" * 60)
print("TROPOSPHERE TITLE VALIDATION BUG DEMONSTRATION")
print("=" * 60)

# Bug 1: Empty string titles are accepted
print("\n1. Empty String Title Bug:")
print("-" * 40)
challenge_empty = pcaconnectorscep.Challenge("", ConnectorArn="arn:aws:pca:us-east-1:123456789:connector/test")
result = challenge_empty.to_dict()
print(f"Created resource with empty title: {repr(challenge_empty.title)}")
print(f"Serialized JSON:\n{json.dumps(result, indent=2)}")
print("❌ BUG: Empty title accepted - CloudFormation requires non-empty logical IDs")

# Bug 2: None titles are accepted  
print("\n2. None Title Bug:")
print("-" * 40)
challenge_none = pcaconnectorscep.Challenge(None, ConnectorArn="arn:aws:pca:us-east-1:123456789:connector/test")
result = challenge_none.to_dict()
print(f"Created resource with None title: {repr(challenge_none.title)}")
print(f"Serialized JSON:\n{json.dumps(result, indent=2)}")
print("❌ BUG: None title accepted - CloudFormation requires string logical IDs")

# Show that the validation exists but isn't triggered
print("\n3. Validation Function Exists But Not Called:")
print("-" * 40)
print("The validate_title() method exists and works correctly when called directly:")
try:
    challenge_empty.validate_title()
except ValueError as e:
    print(f"✓ validate_title() correctly rejects empty: {e}")

try:
    challenge_none.validate_title()
except ValueError as e:
    print(f"✓ validate_title() correctly rejects None: {e}")

print("\n4. Root Cause Analysis:")
print("-" * 40)
print("The bug is in __init__ (line 183-184):")
print("    if self.title:")
print("        self.validate_title()")
print("")
print("This skips validation when title is falsy (empty string, None, etc.)")
print("Should be: self.validate_title() # Always validate for AWSObject")

print("\n5. Impact:")
print("-" * 40)
print("• Invalid CloudFormation templates can be generated")
print("• Templates with empty/None logical IDs will fail at deploy time")
print("• Late error detection - fails at AWS API call instead of object creation")

print("\n" + "=" * 60)