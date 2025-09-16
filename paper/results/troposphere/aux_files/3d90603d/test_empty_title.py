#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.pcaconnectorscep as pcaconnectorscep
import json

# Test empty string as title
print("Testing empty string as title...")
try:
    challenge = pcaconnectorscep.Challenge("", ConnectorArn="arn:test")
    print(f"Created Challenge with empty title: {repr(challenge.title)}")
    
    # Try to serialize it
    challenge_dict = challenge.to_dict()
    print(f"Serialized successfully: {json.dumps(challenge_dict, indent=2)}")
    
    # This is a bug - CloudFormation logical IDs cannot be empty
    print("\nBUG FOUND: Empty title is accepted but should be rejected!")
    print("CloudFormation logical resource names cannot be empty.")
    
except ValueError as e:
    print(f"Correctly rejected empty title: {e}")

# Test None as title  
print("\n\nTesting None as title...")
try:
    challenge = pcaconnectorscep.Challenge(None, ConnectorArn="arn:test")
    print(f"Created Challenge with None title: {repr(challenge.title)}")
    
    challenge_dict = challenge.to_dict()
    print(f"Serialized successfully: {json.dumps(challenge_dict, indent=2)}")
    
    print("\nBUG FOUND: None title is accepted!")
    
except (ValueError, TypeError) as e:
    print(f"Correctly rejected None title: {e}")

# Test whitespace-only title
print("\n\nTesting whitespace-only title...")
for ws_title in ["   ", "\t", "\n", "  \t  "]:
    try:
        challenge = pcaconnectorscep.Challenge(ws_title, ConnectorArn="arn:test")
        print(f"Created Challenge with whitespace title: {repr(challenge.title)}")
        
        challenge_dict = challenge.to_dict()
        print(f"Serialized successfully for {repr(ws_title)}")
        
        print(f"BUG: Whitespace-only title {repr(ws_title)} is accepted!")
        
    except ValueError as e:
        print(f"Correctly rejected whitespace title {repr(ws_title)}: {e}")