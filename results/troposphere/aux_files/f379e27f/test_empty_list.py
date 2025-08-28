#!/usr/bin/env python3
"""Test empty list behavior."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.oam as oam

# Test empty list for ResourceTypes
print("Testing empty list for ResourceTypes...")

try:
    link = oam.Link('TestLink', ResourceTypes=[], SinkIdentifier='test')
    print(f"✓ Empty list accepted: {link.ResourceTypes}")
    print(f"  to_dict: {link.to_dict()}")
except TypeError as e:
    print(f"✗ TypeError raised: {e}")
except Exception as e:
    print(f"✗ Other error: {e}")

# Test with wrong type elements
print("\nTesting list with integers...")
try:
    link = oam.Link('TestLink', ResourceTypes=[1, 2, 3], SinkIdentifier='test')
    print(f"✓ Integer list accepted: {link.ResourceTypes}")
except TypeError as e:
    print(f"✗ TypeError raised: {e}")

# Test with string (not list)
print("\nTesting string instead of list...")
try:
    link = oam.Link('TestLink', ResourceTypes='not-a-list', SinkIdentifier='test')
    print(f"✓ String accepted: {link.ResourceTypes}")
except TypeError as e:
    print(f"✗ TypeError raised: {e}")