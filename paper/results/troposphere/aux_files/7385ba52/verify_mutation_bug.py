#!/usr/bin/env python3
"""Verify that Tags concatenation mutates the right operand."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

from troposphere import Tags

# Create two Tags objects
tags1 = Tags(**{'key1': 'value1'})
tags2 = Tags(**{'key2': 'value2'})

print("BEFORE concatenation:")
print("tags1.tags:", tags1.tags)
print("tags2.tags:", tags2.tags)
print("len(tags1.tags):", len(tags1.tags))
print("len(tags2.tags):", len(tags2.tags))
print()

# Concatenate
combined = tags1 + tags2

print("AFTER concatenation (tags1 + tags2):")
print("tags1.tags:", tags1.tags)
print("tags2.tags:", tags2.tags)  # This should be unchanged but it's not!
print("combined.tags:", combined.tags)
print("len(tags1.tags):", len(tags1.tags))
print("len(tags2.tags):", len(tags2.tags))  # This should still be 1 but it's not!
print("len(combined.tags):", len(combined.tags))
print()

# Check if tags2 is the same object as combined
print("Is tags2 the same object as combined?", tags2 is combined)
print("Are tags2.tags and combined.tags the same list?", tags2.tags is combined.tags)

# The bug is that the __add__ method modifies tags2 instead of creating a new Tags object!