#!/usr/bin/env python3
"""Test to understand CloudFormation's actual requirements."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
import re

# CloudFormation documentation states that logical IDs must be alphanumeric (A-Za-z0-9)
# and unique within the template. Let's verify this matches troposphere's implementation.

print("CloudFormation Logical ID Requirements:")
print("- Must be alphanumeric (A-Za-z0-9)")
print("- Must be unique within the template")
print()

# Check the regex pattern
pattern = re.compile(r"^[a-zA-Z0-9]+$")

print("Troposphere's regex pattern: r'^[a-zA-Z0-9]+$'")
print()

# Test cases that should work according to CloudFormation
valid_cases = [
    "MyResource",
    "Resource123",
    "EC2Instance1",
    "S3Bucket2024",
    "RDSDatabase"
]

print("Testing valid CloudFormation logical IDs:")
for case in valid_cases:
    matches_regex = pattern.match(case) is not None
    print(f"  '{case}': {'✓ Passes' if matches_regex else '✗ Fails'}")

print()

# Test cases that should NOT work according to CloudFormation
invalid_cases = [
    "My-Resource",  # Contains hyphen
    "My_Resource",  # Contains underscore
    "My.Resource",  # Contains period
    "My Resource",  # Contains space
    "Resource#1",   # Contains hash
    "été",          # Contains accented characters
    "Ресурс",       # Cyrillic characters
    "资源",         # Chinese characters
    "π",            # Greek letter
    "µService",     # Contains Greek mu
]

print("Testing invalid CloudFormation logical IDs:")
for case in invalid_cases:
    matches_regex = pattern.match(case) is not None
    is_alnum = case.replace('-', '').replace('_', '').replace('.', '').replace(' ', '').replace('#', '').isalnum()
    print(f"  '{case}': Regex={'✓' if matches_regex else '✗'}, Python isalnum={is_alnum}")