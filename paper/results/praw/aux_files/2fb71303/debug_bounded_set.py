#!/usr/bin/env python3
"""Debug the BoundedSet LRU behavior."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from praw.models.util import BoundedSet

# Reproduce the failing test case
max_size = 4
initial_items = [0, 1, 2, 3, 4]

bounded_set = BoundedSet(max_size)

print(f"Max size: {max_size}")
print(f"Initial items: {initial_items}")
print("\nAdding items one by one:")
print("-" * 40)

for i, item in enumerate(initial_items[:max_size + 2]):
    bounded_set.add(item)
    print(f"Added {item}: set = {list(bounded_set._set.keys())}, size = {len(bounded_set._set)}")

print("\nChecking which items are in the set:")
print("-" * 40)

for i, item in enumerate(initial_items[:max_size + 2]):
    in_set = item in bounded_set
    print(f"Item {item} (index {i}): {'IN' if in_set else 'NOT IN'} set")

print("\nExpected behavior:")
print("-" * 40)
print("We added 6 items (indices 0-5) with max_size=4")
print("The first 2 items (0, 1) should have been evicted")
print("Items 2, 3, 4, 5 should remain")

print("\nActual contents of set:")
print(list(bounded_set._set.keys()))

print("\nDEBUG: Let's trace what happens with 'in' operator:")
print("-" * 40)

# Create fresh set
bounded_set2 = BoundedSet(4)
for item in [0, 1, 2, 3, 4]:
    bounded_set2.add(item)

print(f"After adding [0,1,2,3,4]: {list(bounded_set2._set.keys())}")

# Now check if 0 is in set - this calls __contains__ which calls _access
print(f"Checking if 0 is in set...")
result = 0 in bounded_set2
print(f"Result: {result}")
print(f"After checking: {list(bounded_set2._set.keys())}")

if result:
    print("\nBUG FOUND: Item 0 was in the set when it shouldn't be!")
    print("OR: The __contains__ method modified the set during lookup!")
    
    # Let's check what _access does
    print("\nLet's see what happens with _access:")
    bounded_set3 = BoundedSet(3)
    bounded_set3.add(1)
    bounded_set3.add(2) 
    bounded_set3.add(3)
    print(f"Set before _access: {list(bounded_set3._set.keys())}")
    
    # Access item 1 (which is in set)
    bounded_set3._access(1)
    print(f"After _access(1): {list(bounded_set3._set.keys())}")
    
    # The _access method moves accessed items to the end!
    # This means checking with 'in' modifies the LRU order!