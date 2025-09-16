#!/usr/bin/env python3
"""Advanced test for potential hash bugs in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import troposphere.codestarnotifications as csn
from hypothesis import given, strategies as st

print("=" * 60)
print("Advanced hash bug testing")
print("=" * 60)

# Test 1: Inconsistent hash after modification
print("\nTest 1: Hash stability after property modification")
print("-" * 40)

target = csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:topic", TargetType="SNS")
original_hash = hash(target)
original_dict = target.to_dict()

print(f"Original hash: {original_hash}")
print(f"Original dict: {original_dict}")

# Try to modify a property
try:
    target.TargetAddress = "arn:aws:sns:us-east-1:123456789012:new-topic"
    new_hash = hash(target)
    new_dict = target.to_dict()
    
    print(f"New hash after modification: {new_hash}")
    print(f"New dict after modification: {new_dict}")
    
    if original_hash == new_hash and original_dict != new_dict:
        print("✗ BUG: Hash didn't change despite property change!")
    else:
        print("✓ Hash changed when property changed")
except Exception as e:
    print(f"Could not modify property: {e}")

# Test 2: Hash collision with None vs empty string title
print("\n" + "=" * 60)
print("Test 2: Hash behavior with None vs empty string title")
print("-" * 40)

# Objects created without title have None
target_none = csn.Target(TargetAddress="arn:test", TargetType="SNS")
print(f"Target with None title: title={target_none.title}, hash={hash(target_none)}")

# Try to create with empty string title (if allowed)
try:
    # AWSProperty doesn't require a title in __init__
    target_empty = csn.Target(title="", TargetAddress="arn:test", TargetType="SNS")
    print(f"Target with empty title: title='{target_empty.title}', hash={hash(target_empty)}")
    
    if target_none == target_empty:
        print("✗ Objects with None and empty title are considered equal")
    else:
        print("✓ Objects with None and empty title are different")
except Exception as e:
    print(f"Could not create with empty title: {e}")

# Test 3: Hash behavior with validation disabled
print("\n" + "=" * 60)
print("Test 3: Hash behavior with validation disabled")
print("-" * 40)

target1 = csn.Target(TargetAddress="arn:test", TargetType="SNS")
target2 = csn.Target(TargetAddress="arn:test", TargetType="SNS")

# Disable validation
target1_no_val = target1.no_validation()
target2_no_val = target2.no_validation()

hash1 = hash(target1_no_val)
hash2 = hash(target2_no_val)

print(f"hash(target1_no_validation): {hash1}")
print(f"hash(target2_no_validation): {hash2}")

if hash1 == hash2:
    print("✓ Hashes are equal with validation disabled")
else:
    print("✗ BUG: Hashes differ with validation disabled")

# Test 4: JSON serialization edge cases
print("\n" + "=" * 60)
print("Test 4: JSON serialization edge cases")
print("-" * 40)

# Test with special characters that might affect JSON
special_arn = 'arn:aws:sns:us-east-1:123456789012:topic-with-"quotes"'
target_special = csn.Target(TargetAddress=special_arn, TargetType="SNS")

try:
    json_str = json.dumps(target_special.to_dict())
    print(f"✓ Special characters handled in JSON: {json_str[:50]}...")
except Exception as e:
    print(f"✗ JSON serialization failed: {e}")

# Test 5: Hash consistency in collections
print("\n" + "=" * 60)
print("Test 5: Hash consistency in NotificationRule with Targets")
print("-" * 40)

target_a = csn.Target(TargetAddress="arn:a", TargetType="SNS")
target_b = csn.Target(TargetAddress="arn:b", TargetType="SNS")

rule1 = csn.NotificationRule(
    "TestRule",
    Name="Test",
    DetailType="BASIC",
    EventTypeIds=["event1"],
    Resource="arn:resource",
    Targets=[target_a, target_b]
)

# Create identical rule
rule2 = csn.NotificationRule(
    "TestRule",
    Name="Test", 
    DetailType="BASIC",
    EventTypeIds=["event1"],
    Resource="arn:resource",
    Targets=[target_a, target_b]
)

hash1 = hash(rule1)
hash2 = hash(rule2)

print(f"hash(rule1): {hash1}")
print(f"hash(rule2): {hash2}")

if rule1 == rule2:
    if hash1 == hash2:
        print("✓ Equal rules have equal hashes")
    else:
        print("✗ BUG: Equal rules have different hashes!")
else:
    print("✗ Rules with same properties are not equal")

# Test 6: Mutable property issue
print("\n" + "=" * 60)
print("Test 6: Hash mutability issue")
print("-" * 40)

# Put object in set, then try to find it after property access
target = csn.Target(TargetAddress="arn:test", TargetType="SNS")
target_set = {target}

# Access properties (shouldn't change hash)
_ = target.TargetAddress
_ = target.TargetType
_ = target.to_dict()

if target in target_set:
    print("✓ Object still found in set after property access")
else:
    print("✗ BUG: Object not found in set after property access!")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("Completed advanced hash testing for troposphere.codestarnotifications")