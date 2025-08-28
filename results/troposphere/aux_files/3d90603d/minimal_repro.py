#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.pcaconnectorscep as pcaconnectorscep

# Test case 1: Greek letter mu (µ) - valid Unicode letter
try:
    challenge = pcaconnectorscep.Challenge("µ", ConnectorArn="arn:test")
    print("SUCCESS: Created Challenge with title 'µ'")
except ValueError as e:
    print(f"FAILURE: Cannot create Challenge with Unicode letter 'µ': {e}")

# Test case 2: Regular ASCII letters work fine  
try:
    challenge = pcaconnectorscep.Challenge("TestChallenge", ConnectorArn="arn:test")
    print("SUCCESS: Created Challenge with ASCII title 'TestChallenge'")
except ValueError as e:
    print(f"FAILURE: Cannot create Challenge with ASCII title: {e}")

# Test case 3: Numbers work
try:
    challenge = pcaconnectorscep.Challenge("Test123", ConnectorArn="arn:test")
    print("SUCCESS: Created Challenge with alphanumeric title 'Test123'")
except ValueError as e:
    print(f"FAILURE: Cannot create Challenge with alphanumeric title: {e}")

# Test case 4: Other Unicode letters
test_cases = [
    ("Ω", "Greek capital omega"),
    ("π", "Greek small pi"),
    ("ñ", "Spanish n with tilde"),
    ("ü", "German u with umlaut"),
    ("中", "Chinese character"),
    ("א", "Hebrew aleph"),
    ("🦄", "Emoji (not a letter)"),
]

for char, description in test_cases:
    try:
        challenge = pcaconnectorscep.Challenge(char, ConnectorArn="arn:test")
        print(f"SUCCESS: Created Challenge with {description} '{char}'")
    except ValueError as e:
        print(f"FAILURE: Cannot create Challenge with {description} '{char}'")

print("\n--- Analysis ---")
print("The validate_title() method uses regex ^[a-zA-Z0-9]+$ which only accepts:")
print("- ASCII letters (a-z, A-Z)")
print("- Digits (0-9)")
print("\nIt rejects all non-ASCII Unicode letters, even though they are valid letter characters.")
print("CloudFormation logical names actually support Unicode letters in many contexts.")