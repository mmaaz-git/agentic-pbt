#!/usr/bin/env python3
"""Reproduce the Tags bug in troposphere.globalaccelerator"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.globalaccelerator import Accelerator
from troposphere import Tags

# Test 1: Empty tags dict causes issue
print("Test 1: Creating Accelerator with empty tags dict")
tags = {}
try:
    acc = Accelerator(
        title="TestAcc",
        Name="TestName",
        Tags=Tags(tags) if tags else None  # This evaluates to Tags({}) when tags={}
    )
    print("Success - created accelerator")
except Exception as e:
    print(f"Failed: {e}")

print("\nTest 2: Tags({}) returns truthy value")
empty_tags = Tags({})
print(f"Tags({{}}) is truthy: {bool(empty_tags)}")
print(f"Tags({{}}) == None: {empty_tags == None}")

print("\nTest 3: Setting Tags=None directly")
try:
    acc = Accelerator(
        title="TestAcc",
        Name="TestName",
        Tags=None
    )
    print("Success - created accelerator with Tags=None")
except Exception as e:
    print(f"Failed with Tags=None: {e}")

print("\nTest 4: Not setting Tags at all")
try:
    acc = Accelerator(
        title="TestAcc",
        Name="TestName"
    )
    print("Success - created accelerator without Tags")
except Exception as e:
    print(f"Failed without Tags: {e}")

print("\nTest 5: Setting Tags to empty Tags object")
try:
    acc = Accelerator(
        title="TestAcc",  
        Name="TestName",
        Tags=Tags({})
    )
    print("Success - created accelerator with Tags({})")
    print(f"to_dict result: {acc.to_dict()}")
except Exception as e:
    print(f"Failed with Tags({{}}): {e}")