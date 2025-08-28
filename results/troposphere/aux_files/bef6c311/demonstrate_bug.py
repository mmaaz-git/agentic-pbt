#!/usr/bin/env python3
"""Minimal demonstration of hash/equality bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ce as ce

# Create two identical ResourceTag objects
tag1 = ce.ResourceTag(Key="TestKey", Value="TestValue")
tag2 = ce.ResourceTag(Key="TestKey", Value="TestValue")

print("Created two identical ResourceTag objects:")
print(f"tag1: Key={tag1.Key}, Value={tag1.Value}")
print(f"tag2: Key={tag2.Key}, Value={tag2.Value}")

# Test equality
print(f"\ntag1 == tag2: {tag1 == tag2}")

# Test hash
print(f"hash(tag1): {hash(tag1)}")
print(f"hash(tag2): {hash(tag2)}")
print(f"hash(tag1) == hash(tag2): {hash(tag1) == hash(tag2)}")

# Demonstrate the problem with sets
tag_set = set()
tag_set.add(tag1)
tag_set.add(tag2)
print(f"\nSet containing both identical tags has {len(tag_set)} element(s)")
print("Expected: 1 (since they are equal)")

if len(tag_set) != 1:
    print("\n✗ BUG CONFIRMED: Equal objects have different hashes!")
    print("This violates Python's requirement that equal objects must have equal hashes.")
    print("Impact: These objects cannot be used reliably in sets or as dictionary keys.")