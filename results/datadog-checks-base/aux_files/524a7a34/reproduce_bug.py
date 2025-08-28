#!/usr/bin/env python3
"""Minimal reproduction of pattern_filter bug"""

import re

def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    """This filters `items` by a regular expression `whitelist` and/or
    `blacklist`, with the `blacklist` taking precedence. An optional `key`
    function can be provided that will be passed each item.
    """
    def __return_self(obj):
        return obj
    
    def _filter(items, pattern_list, key):
        return {key(item) for pattern in pattern_list for item in items if re.search(pattern, key(item))}
    
    key = key or __return_self
    if whitelist:
        whitelisted = _filter(items, whitelist, key)

        if blacklist:
            blacklisted = _filter(items, blacklist, key)
            # Remove any blacklisted items from the whitelisted ones.
            whitelisted.difference_update(blacklisted)

        return [item for item in items if key(item) in whitelisted]

    elif blacklist:
        blacklisted = _filter(items, blacklist, key)
        return [item for item in items if key(item) not in blacklisted]

    else:
        return items

# Reproduce the bug
print("Testing pattern_filter with duplicate items...")
items = ['00', '0', '00']
whitelist = None

result = pattern_filter(items, whitelist=whitelist)
print(f"Input items: {items}")
print(f"Result: {result}")

# Check order preservation
print("\nChecking order preservation...")
indices = [items.index(r) for r in result]
print(f"Indices of result items in original: {indices}")
print(f"Sorted indices: {sorted(indices)}")
print(f"Order preserved? {indices == sorted(indices)}")

# The bug occurs because items.index() always returns the FIRST occurrence
# So for ['00', '0', '00'], the indices are:
# - '00' -> index 0 (first occurrence)
# - '0' -> index 1
# - '00' -> index 0 (first occurrence again, not index 2!)

print("\n--- Bug Explanation ---")
print("The issue is that when there are duplicate items in the input,")
print("using items.index(r) always returns the index of the FIRST occurrence.")
print("So for duplicate items, we get incorrect indices that don't reflect")
print("the actual order in the result list.")

print("\n--- Expected vs Actual ---")
print("Input: ['00', '0', '00']")
print("Expected indices: [0, 1, 2] (reflecting actual positions)")
print("Actual indices: [0, 1, 0] (always finding first occurrence)")

# Test with another example
print("\n--- Another Example ---")
items2 = ['a', 'b', 'a', 'c', 'a']
result2 = pattern_filter(items2, whitelist=None)
print(f"Input: {items2}")
print(f"Result: {result2}")
indices2 = [items2.index(r) for r in result2]
print(f"Indices: {indices2}")
print(f"Order preserved? {indices2 == sorted(indices2)}")

# This is actually not a bug in pattern_filter itself!
# The bug is in my test - I was using a flawed method to check order preservation.
# The function returns items in the same order they appear in the input,
# but when there are duplicates, items.index() doesn't give us the right indices.

print("\n--- Correction ---")
print("Actually, this might be a FALSE POSITIVE in my test!")
print("The pattern_filter function IS preserving order correctly.")
print("The issue is with my test method using items.index() for duplicates.")

# Let's verify this by manually checking
print("\n--- Manual Verification ---")
print("Input: ['00', '0', '00']")
print("Output: ['00', '0', '00']")
print("Order IS preserved - items appear in same order as input.")
print("The test was flawed, not the function!")