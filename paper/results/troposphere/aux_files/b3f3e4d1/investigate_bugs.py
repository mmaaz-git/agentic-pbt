#!/usr/bin/env python3
"""Investigate the bugs found in troposphere.launchwizard"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import launchwizard, Tags

print("Bug 1: Title validation with Unicode characters")
print("-" * 50)

# This should work according to Python's isalnum() but fails
try:
    deployment = launchwizard.Deployment(
        "µ",  # micro sign - Unicode letter
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload"
    )
    print("✓ Deployment created with title 'µ'")
except ValueError as e:
    print(f"✗ Failed to create deployment with title 'µ': {e}")

# Check what Python considers alphanumeric
print(f"\nPython's 'µ'.isalnum() = {'µ'.isalnum()}")
print(f"Python's 'µ'.isalpha() = {'µ'.isalpha()}")

print("\n" + "="*50)
print("Bug 2: Empty Tags dict becomes None")
print("-" * 50)

# Create deployment with empty tags dict
tags = {}
tag_obj = Tags(**tags) if tags else None
print(f"Empty dict {{}} -> Tags object: {tag_obj}")
print(f"Type: {type(tag_obj)}")

# This fails because Tags(None) is not acceptable
try:
    deployment = launchwizard.Deployment(
        "Test",
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload",
        Tags=tag_obj
    )
    print("✓ Deployment created with empty Tags")
except TypeError as e:
    print(f"✗ Failed to create deployment with empty Tags: {e}")

# But this works - Tags with empty dict
try:
    deployment = launchwizard.Deployment(
        "Test2",
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload",
        Tags=Tags()  # Empty Tags object
    )
    print("✓ Deployment created with Tags()")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "="*50)
print("Bug 3: Inconsistency in title validation")
print("-" * 50)

# The regex used is ^[a-zA-Z0-9]+$
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

test_strings = [
    ("ABC123", "ASCII alphanumeric"),
    ("µ", "Unicode letter (micro)"),
    ("Ω", "Unicode letter (omega)"),
    ("test_name", "With underscore"),
    ("", "Empty string"),
    ("123", "Only digits"),
    ("ñ", "Latin letter with tilde"),
]

for s, desc in test_strings:
    regex_match = bool(valid_names.match(s))
    py_alnum = s.isalnum()
    print(f"{s:15} | {desc:25} | Regex: {regex_match:5} | isalnum(): {py_alnum:5}")

print("\nThe validation uses regex ^[a-zA-Z0-9]+$ but Python's isalnum() accepts Unicode")