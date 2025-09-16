#!/usr/bin/env python3
"""Test whether this is a real bug that affects CloudFormation template generation."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.lookoutequipment as le
import json

# Test 1: Can we create a template with ASCII names?
print("Test 1: Creating template with ASCII names...")
try:
    scheduler = le.InferenceScheduler(
        "MyScheduler",
        DataInputConfiguration=le.DataInputConfiguration(
            S3InputConfiguration=le.S3InputConfiguration(Bucket="test-bucket")
        ),
        DataOutputConfiguration=le.DataOutputConfiguration(
            S3OutputConfiguration=le.S3OutputConfiguration(Bucket="test-bucket")
        ),
        DataUploadFrequency="PT1H",
        ModelName="test-model",
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    template_dict = scheduler.to_dict()
    print("Success! Template created.")
    print(json.dumps(template_dict, indent=2))
except Exception as e:
    print(f"Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 2: What happens with Unicode names?
print("Test 2: Attempting to create template with Unicode names...")
try:
    scheduler = le.InferenceScheduler(
        "MySchedulerπ",  # Contains Greek letter pi
        DataInputConfiguration=le.DataInputConfiguration(
            S3InputConfiguration=le.S3InputConfiguration(Bucket="test-bucket")
        ),
        DataOutputConfiguration=le.DataOutputConfiguration(
            S3OutputConfiguration=le.S3OutputConfiguration(Bucket="test-bucket")
        ),
        DataUploadFrequency="PT1H",
        ModelName="test-model",
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    template_dict = scheduler.to_dict()
    print("Unexpectedly succeeded! Template created.")
    print(json.dumps(template_dict, indent=2))
except ValueError as e:
    print(f"Failed as expected: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Check error message accuracy
print("Test 3: Checking error message accuracy...")
test_cases = [
    ('µ', 'Greek letter mu'),
    ('π', 'Greek letter pi'),
    ('①', 'Circled digit one'),
    ('Ⅲ', 'Roman numeral three'),
    ('ñ', 'Spanish n with tilde'),
    ('café', 'Word with accent'),
]

for char, description in test_cases:
    is_alnum = char.isalnum() or all(c.isalnum() or c.isspace() for c in char)
    try:
        config = le.S3InputConfiguration(
            title=char,
            Bucket='test-bucket'
        )
        result = "Accepted"
    except ValueError as e:
        result = "Rejected"
    print(f"  '{char}' ({description}): Python isalnum={is_alnum}, Troposphere={result}")