#!/usr/bin/env python3
"""Test for potential hash/equality bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ce as ce

# Test Case 1: Hash consistency with None title
print("=" * 50)
print("Test 1: Hash consistency with None title")
print("=" * 50)

# Create two identical ResourceTags, both without explicit title
tag1 = ce.ResourceTag(Key="TestKey", Value="TestValue")
tag2 = ce.ResourceTag(Key="TestKey", Value="TestValue")

print(f"tag1.title: {tag1.title}")
print(f"tag2.title: {tag2.title}")
print(f"tag1.to_dict(): {tag1.to_dict()}")
print(f"tag2.to_dict(): {tag2.to_dict()}")

# Check equality
if tag1 == tag2:
    print("✓ Tags are equal")
else:
    print("✗ BUG: Identical tags are not equal!")

# Check hash consistency
hash1 = hash(tag1)
hash2 = hash(tag2)
print(f"hash(tag1): {hash1}")
print(f"hash(tag2): {hash2}")

if hash1 == hash2:
    print("✓ Hashes are equal")
else:
    print("✗ BUG: Identical objects have different hashes!")

# Test Case 2: Set membership
print("\n" + "=" * 50)
print("Test 2: Set membership")
print("=" * 50)

# Create a set with one tag
tag_set = {tag1}
print(f"Created set with tag1")

# Check if identical tag is in set
if tag2 in tag_set:
    print("✓ tag2 found in set containing tag1")
else:
    print("✗ BUG: Identical tag not found in set!")

# Add tag2 to set
tag_set.add(tag2)
print(f"Added tag2 to set")
print(f"Set size: {len(tag_set)}")

if len(tag_set) == 1:
    print("✓ Set correctly recognizes identical objects")
else:
    print("✗ BUG: Set contains duplicates of identical objects!")

# Test Case 3: Dictionary keys
print("\n" + "=" * 50)
print("Test 3: Dictionary keys")
print("=" * 50)

tag_dict = {tag1: "value1"}
print("Created dict with tag1 as key")

# Try to access with identical tag
try:
    value = tag_dict[tag2]
    print(f"✓ Retrieved value using tag2: {value}")
except KeyError:
    print("✗ BUG: Cannot use identical object as dictionary key!")

# Test Case 4: Equality with dict
print("\n" + "=" * 50)
print("Test 4: Equality with dict representation")
print("=" * 50)

dict_repr = tag1.to_dict()
print(f"Dict representation: {dict_repr}")

if tag1 == dict_repr:
    print("✓ Tag equals its dict representation")
else:
    print("✗ Tag does not equal its dict representation")

# Check the reverse
if dict_repr == tag1:
    print("✓ Dict representation equals tag")
else:
    print("✗ Dict representation does not equal tag")

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print("If any ✗ marks appear above, there are bugs in the hash/equality implementation")