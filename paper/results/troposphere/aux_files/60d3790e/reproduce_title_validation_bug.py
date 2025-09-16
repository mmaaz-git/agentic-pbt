#!/usr/bin/env python3
"""
Minimal reproduction of title validation bug in troposphere
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codeconnections import Connection

# Create a Connection with an invalid title containing special characters
# CloudFormation resource names must be alphanumeric only
conn = Connection("my-invalid-title!", ConnectionName="ValidConnectionName")

# This should fail because the title contains hyphens and exclamation mark
# but it doesn't - this is the bug
result = conn.to_dict(validation=True)

print("BUG: Connection.to_dict() accepted invalid title 'my-invalid-title!'")
print(f"Generated CloudFormation template with invalid resource name:")
print(f"Resource name in template: {list(result.keys())[0] if result else 'N/A'}")
print(f"Full output: {result}")

# The validate_title() method exists and would catch this:
try:
    conn.validate_title()
    print("\nEven validate_title() didn't catch it - severe bug!")
except ValueError as e:
    print(f"\nvalidate_title() correctly rejects it: {e}")
    print("This proves to_dict() doesn't call validate_title()")