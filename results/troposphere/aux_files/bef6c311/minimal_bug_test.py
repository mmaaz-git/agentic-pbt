#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ce as ce

# Simple test - try to create ResourceTag
print("Creating ResourceTag...")
tag = ce.ResourceTag(Key="TestKey", Value="TestValue")
print(f"Success: {tag.to_dict()}")

# Test missing required field
print("\nTesting missing required field...")
try:
    bad_tag = ce.ResourceTag(Key="OnlyKey")
    bad_tag.to_dict()
    print("BUG: Should have failed!")
except Exception as e:
    print(f"Correctly failed: {e}")