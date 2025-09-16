#!/usr/bin/env python3
"""Investigate the Tags concatenation bug in detail."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Tags

print("Investigating Tags concatenation bug")
print("=" * 50)

# Test 1: Same key, different values
tags1 = Tags({'Environment': 'prod'})
tags2 = Tags({'Environment': 'dev'})

print("Before concatenation:")
print(f"tags1.tags: {tags1.tags}")
print(f"tags2.tags: {tags2.tags}")

combined = tags1 + tags2
print("\nAfter concatenation (tags1 + tags2):")
print(f"combined.tags: {combined.tags}")

print("\n" + "-" * 50)
print("The issue: __add__ method implementation")
print("-" * 50)

# Looking at the __add__ implementation (line 743-745 in __init__.py):
# def __add__(self, newtags: Tags) -> Tags:
#     newtags.tags = self.tags + newtags.tags
#     return newtags

print("The __add__ method modifies newtags in place and returns it!")
print("It does: newtags.tags = self.tags + newtags.tags")
print("This concatenates the lists, BUT it modifies the second operand!")

# Demonstrate the mutation
tags3 = Tags({'Key1': 'Value1'})
tags4 = Tags({'Key2': 'Value2'})
print(f"\nBefore: tags4.tags = {tags4.tags}")
result = tags3 + tags4
print(f"After tags3 + tags4: tags4.tags = {tags4.tags}")
print(f"Result is tags4: {result is tags4}")

print("\nBUG: The + operator mutates the right operand instead of creating a new object!")
print("This violates the principle that + should not modify its operands.")