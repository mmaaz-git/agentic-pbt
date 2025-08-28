#!/usr/bin/env python3
"""Investigate the item_hash behavior more carefully."""

import sys
import json
import hashlib

# Add the rpdk path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')


def test_sort_behavior():
    """Test what .sort() actually returns."""
    lst = [3, 1, 2]
    result = lst.sort()
    print(f"lst.sort() returns: {result} (type: {type(result)})")
    print(f"Original list after sort: {lst}")
    
    # What the buggy code does
    buggy_result = [3, 1, 2].sort()
    print(f"\n[3, 1, 2].sort() returns: {buggy_result}")
    
    # Try to json.dumps None
    print(f"\njson.dumps(None) = {json.dumps(None)}")
    

def trace_item_hash():
    """Trace through item_hash to understand the flow."""
    from rpdk.core.jsonutils.utils import item_hash
    
    # Add some debug output
    original_code = '''
def item_hash(item):
    dhash = hashlib.md5()
    if isinstance(item, dict):
        item = {k: item_hash(v) for k, v in item.items()}
    if isinstance(item, list):
        item = [item_hash(i) for i in item].sort()
    encoded = json.dumps(item, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()
'''
    
    print("Original code has this bug on line 32:")
    print("    item = [item_hash(i) for i in item].sort()")
    print("\nThis sets item = None when item is a list!")
    
    # Test with actual function
    test_cases = [
        [1, 2, 3],
        [],
        [{"a": 1}],
        [[1, 2], [3, 4]]
    ]
    
    for test in test_cases:
        print(f"\nTesting {test}:")
        try:
            result = item_hash(test)
            print(f"  Result: {result}")
            
            # The fact that this works means json.dumps(None) = "null"
            # which gets hashed consistently
        except Exception as e:
            print(f"  Error: {e}")


def test_actual_bug_impact():
    """Test the actual impact of the bug."""
    from rpdk.core.jsonutils.utils import item_hash
    
    print("The bug causes all lists to hash to the same value!")
    print("Because they all become None, which json.dumps as 'null'\n")
    
    list1 = [1, 2, 3]
    list2 = [4, 5, 6]
    list3 = ["a", "b", "c"]
    list4 = [{"complex": "object"}, {"another": "one"}]
    empty_list = []
    
    hash1 = item_hash(list1)
    hash2 = item_hash(list2)
    hash3 = item_hash(list3)
    hash4 = item_hash(list4)
    hash5 = item_hash(empty_list)
    
    print(f"item_hash([1, 2, 3]) = {hash1}")
    print(f"item_hash([4, 5, 6]) = {hash2}")
    print(f"item_hash(['a', 'b', 'c']) = {hash3}")
    print(f"item_hash([{{'complex': 'object'}}, {{'another': 'one'}}]) = {hash4}")
    print(f"item_hash([]) = {hash5}")
    
    if hash1 == hash2 == hash3 == hash4 == hash5:
        print("\n❌ BUG CONFIRMED: All lists hash to the same value!")
        print("This is because .sort() returns None, so all lists become None")
        return True
    else:
        print("\n✓ Hashes are different (unexpected)")
        return False


if __name__ == "__main__":
    test_sort_behavior()
    print("\n" + "="*50)
    trace_item_hash()
    print("\n" + "="*50)
    bug_found = test_actual_bug_impact()