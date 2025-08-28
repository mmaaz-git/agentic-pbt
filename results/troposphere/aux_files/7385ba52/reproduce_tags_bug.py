#!/usr/bin/env python3
"""Minimal reproduction of the Tags concatenation bug."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

from troposphere import Tags

# Test case found by Hypothesis
tags1 = Tags(**{'0': ''})
tags2 = Tags(**{'0': ''})

print("tags1 dict:", {'0': ''})
print("tags2 dict:", {'0': ''})
print()

print("tags1.to_dict():", tags1.to_dict())
print("tags2.to_dict():", tags2.to_dict())
print()

# Concatenate
combined = tags1 + tags2

print("Combined tags.to_dict():", combined.to_dict())
print("Expected length:", len(tags1.to_dict()) + len(tags2.to_dict()))
print("Actual length:", len(combined.to_dict()))
print()

# What should happen: AWS Tags allow duplicate keys with different values
# The concatenation should preserve all tags from both objects
# Expected: [{'Key': '0', 'Value': ''}, {'Key': '0', 'Value': ''}]
# Actual: [{'Key': '0', 'Value': ''}, {'Key': '0', 'Value': ''}] - but check if it's actually 2 or 1

print("Is bug confirmed?", len(combined.to_dict()) != len(tags1.to_dict()) + len(tags2.to_dict()))

# Let's look at the actual tags lists
print("\ntags1.tags:", tags1.tags)
print("tags2.tags:", tags2.tags)
print("combined.tags:", combined.tags)

# More detailed test with different values
print("\n--- Test with different values ---")
tags3 = Tags(**{'key1': 'value1'})
tags4 = Tags(**{'key1': 'value2'})

print("tags3 dict:", {'key1': 'value1'})
print("tags4 dict:", {'key1': 'value2'})

combined2 = tags3 + tags4
print("Combined2 tags:", combined2.to_dict())
print("Expected: Two tags with same key but different values")
print("Actual length:", len(combined2.to_dict()))