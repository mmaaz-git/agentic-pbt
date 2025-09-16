#!/usr/bin/env python3
"""Verify the potential bugs found in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
from troposphere import Parameter

print(f"Verifying bugs in Troposphere {troposphere.__version__}\n")
print("=" * 60)

# Bug 1: Empty title accepted
print("\nBug 1: Testing empty title validation...")
try:
    param = Parameter("", Type="String")
    print(f"BUG CONFIRMED: Empty title was accepted!")
    print(f"  Created parameter with title: '{param.title}'")
except ValueError as e:
    print(f"No bug: Empty title correctly rejected with: {e}")

# Bug 2: String default with Number type
print("\nBug 2: Testing Number parameter with string default...")
try:
    param = Parameter("NumParam", Type="Number", Default="0")
    param.validate()
    print(f"Potential issue: Number parameter accepted string default '0'")
    print(f"  This might be intentional coercion")
    
    # Try with a non-numeric string
    param2 = Parameter("NumParam2", Type="Number", Default="not_a_number")
    try:
        param2.validate()
        print(f"BUG CONFIRMED: Number parameter accepted non-numeric string '{param2.properties['Default']}'")
    except ValueError as e:
        print(f"  Non-numeric strings are correctly rejected: {e}")
except ValueError as e:
    print(f"No bug: String default correctly rejected: {e}")

# Bug 3: Integer default with String type  
print("\nBug 3: Testing String parameter with integer default...")
try:
    param = Parameter("StrParam", Type="String", Default=123)
    param.validate()
    print(f"BUG CONFIRMED: String parameter accepted integer default {param.properties['Default']}")
    print(f"  Type of default: {type(param.properties['Default'])}")
except ValueError as e:
    print(f"No bug: Integer default correctly rejected: {e}")

# Additional test: Title with special characters
print("\nAdditional test: Title with special characters...")
test_titles = [
    ("Test-Name", "hyphen"),
    ("Test_Name", "underscore"),
    ("Test.Name", "dot"),
    ("Test Name", "space"),
    ("Test@Name", "at sign"),
    ("123Test", "starting with number"),
    ("Test123", "ending with number"),
]

for title, desc in test_titles:
    try:
        param = Parameter(title, Type="String")
        print(f"  '{title}' ({desc}): Accepted")
    except ValueError:
        print(f"  '{title}' ({desc}): Rejected")

# Test the actual regex pattern
print("\nTesting the valid_names regex pattern...")
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

test_strings = ["", "Valid123", "Invalid-Name", "Has Space", "Under_score"]
for s in test_strings:
    match = valid_names.match(s)
    print(f"  '{s}': {'Matches' if match else 'Does not match'}")

print("\n" + "=" * 60)