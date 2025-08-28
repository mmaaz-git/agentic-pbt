#!/usr/bin/env python3
"""Debug the item_hash function behavior."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.utils import item_hash

# Test different list orderings
list1 = [3, 1, 2]
list2 = [1, 2, 3]
list3 = [2, 3, 1]

print("Testing item_hash on lists with different orderings:")
print(f"list1 = {list1}, hash = {item_hash(list1)}")
print(f"list2 = {list2}, hash = {item_hash(list2)}")
print(f"list3 = {list3}, hash = {item_hash(list3)}")

print("\nThey should all have the same hash if sorting works correctly.")

# Let's also test what happens with nested lists
nested1 = [[3, 2], [1]]
nested2 = [[1], [3, 2]]
nested3 = [[1], [2, 3]]

print("\nTesting nested lists:")
print(f"nested1 = {nested1}, hash = {item_hash(nested1)}")
print(f"nested2 = {nested2}, hash = {item_hash(nested2)}")
print(f"nested3 = {nested3}, hash = {item_hash(nested3)}")

# Let's trace through what happens
print("\nDebugging the actual code flow:")
test_list = [3, 1, 2]
print(f"Input: {test_list}")

# The bug is on line 32: item = [item_hash(i) for i in item].sort()
# .sort() returns None, so item becomes None
# Then json.dumps(None) would be called

# Let's simulate what the buggy code does:
import hashlib
item = test_list.copy()
if isinstance(item, list):
    result = [item_hash(i) for i in item]
    print(f"After hashing each element: {result}")
    sorted_result = result.copy()
    sorted_result.sort()  # This modifies in place
    print(f"After sorting (correct way): {sorted_result}")
    
    # The buggy way:
    buggy_result = [item_hash(i) for i in test_list].sort()
    print(f"Buggy result (.sort() returns): {buggy_result}")
    
    # So the bug would cause item to become None
    # json.dumps(None) => "null"
    
print("\nWhat json.dumps(None) produces:", json.dumps(None))