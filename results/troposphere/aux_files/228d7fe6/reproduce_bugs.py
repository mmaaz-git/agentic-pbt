#!/usr/bin/env python3
"""Reproduce the bugs found in troposphere.iam validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import iam as iam_validators

print("Bug 1: Group name validator error message says 'Role Name' instead of 'Group Name'")
print("-" * 70)
try:
    # Group name with 129 characters (exceeds 128 limit)
    long_group_name = "a" * 129
    iam_validators.iam_group_name(long_group_name)
except ValueError as e:
    print(f"Error message: {e}")
    print("BUG: Says 'IAM Role Name' but this is for a Group!")

print("\n" + "="*70 + "\n")

print("Bug 2: IAM path validator has format string bug")
print("-" * 70)
try:
    # Path with 513 characters (exceeds 512 limit)
    long_path = "/" + "a" * 511 + "/"
    iam_validators.iam_path(long_path)
except ValueError as e:
    print(f"Exception args: {e.args}")
    print(f"Type of args: {type(e.args)}")
    if isinstance(e.args, tuple) and len(e.args) == 2:
        print("BUG: Format string not properly formatted!")
        print(f"  arg[0]: {e.args[0]}")
        print(f"  arg[1]: {e.args[1][:50]}... (truncated)")

print("\n" + "="*70 + "\n")

print("Bug 3: IAM user name validator has format string bug for invalid names")
print("-" * 70)
try:
    # Invalid user name with special characters
    invalid_name = "user$name"
    iam_validators.iam_user_name(invalid_name)
except ValueError as e:
    print(f"Exception args: {e.args}")
    print(f"Type of args: {type(e.args)}")
    if isinstance(e.args, tuple) and len(e.args) == 2:
        print("BUG: Format string not properly formatted!")
        print(f"  arg[0]: {e.args[0]}")
        print(f"  arg[1]: {e.args[1]}")