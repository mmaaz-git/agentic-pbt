#!/usr/bin/env python3
"""Focused test for hash/equality bug in troposphere.codestarnotifications"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codestarnotifications as csn

print("=" * 60)
print("Testing hash/equality bug in codestarnotifications.Target")
print("=" * 60)

# Create two identical Targets without explicit title
target1 = csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:my-topic", TargetType="SNS")
target2 = csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:my-topic", TargetType="SNS")

print(f"\ntarget1.title: {target1.title}")
print(f"target2.title: {target2.title}")
print(f"\ntarget1.to_dict(): {target1.to_dict()}")
print(f"target2.to_dict(): {target2.to_dict()}")

# Check equality
print("\n" + "-" * 40)
print("Equality check:")
if target1 == target2:
    print("✓ Targets are equal")
else:
    print("✗ BUG: Identical targets are not equal!")

# Check hash consistency
print("\n" + "-" * 40)
print("Hash consistency check:")
hash1 = hash(target1)
hash2 = hash(target2)
print(f"hash(target1): {hash1}")
print(f"hash(target2): {hash2}")

if hash1 == hash2:
    print("✓ Hashes are equal")
else:
    print("✗ BUG: Identical objects have different hashes!")
    print("This violates the Python requirement that equal objects must have equal hashes")

# Test set membership
print("\n" + "-" * 40)
print("Set membership check:")
target_set = {target1}
if target2 in target_set:
    print("✓ target2 found in set containing target1")
else:
    print("✗ BUG: Identical target not found in set!")

target_set.add(target2)
print(f"Set size after adding target2: {len(target_set)}")
if len(target_set) == 1:
    print("✓ Set correctly recognizes identical objects")
else:
    print("✗ BUG: Set contains duplicates of identical objects!")

# Dictionary key test
print("\n" + "-" * 40)
print("Dictionary key check:")
target_dict = {target1: "value1"}
try:
    value = target_dict[target2]
    print(f"✓ Retrieved value using target2: {value}")
except KeyError:
    print("✗ BUG: Cannot use identical object as dictionary key!")

# Test with different properties
print("\n" + "=" * 60)
print("Control test with different properties:")
print("=" * 60)

target3 = csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:different-topic", TargetType="SNS")

print(f"\ntarget3.to_dict(): {target3.to_dict()}")

if target1 != target3:
    print("✓ Different targets are not equal")
else:
    print("✗ BUG: Different targets are incorrectly equal!")

hash3 = hash(target3)
print(f"hash(target3): {hash3}")

# Debugging: Look at the JSON representation used for hashing
print("\n" + "=" * 60)
print("Debug: JSON representation used for hashing")
print("=" * 60)

import json

# From the __hash__ implementation in BaseAWSObject
json1 = json.dumps({"title": target1.title, **target1.to_dict()}, indent=0)
json2 = json.dumps({"title": target2.title, **target2.to_dict()}, indent=0)

print(f"JSON for target1:\n{json1}")
print(f"\nJSON for target2:\n{json2}")

if json1 == json2:
    print("\n✓ JSON representations are identical")
else:
    print("\n✗ JSON representations differ!")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)

bug_found = False
if hash1 != hash2:
    bug_found = True
    print("BUG FOUND: Objects with None title have inconsistent hashes")
    print("This violates the Python contract that equal objects must have equal hashes.")
    print("The bug is in the __hash__ method of BaseAWSObject class.")
    
if not bug_found:
    print("No hash/equality bugs detected in this test.")