#!/usr/bin/env python3
"""Test to demonstrate the bug in item_hash function."""

import sys
import json
import hashlib

# Add the rpdk path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.utils import item_hash


def test_item_hash_list_bug():
    """Demonstrate the bug in item_hash when handling lists."""
    
    # Test 1: Simple list
    simple_list = [1, 2, 3]
    print("Testing simple list:", simple_list)
    try:
        hash_result = item_hash(simple_list)
        print(f"Hash result: {hash_result}")
        
        # The hash should be consistent
        hash_result2 = item_hash(simple_list)
        print(f"Second hash: {hash_result2}")
        assert hash_result == hash_result2, "Hashes should be identical"
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("This error occurs because .sort() returns None, not the sorted list")
        
    # Test 2: Try what the correct implementation would produce
    print("\n--- What the correct implementation should do ---")
    def item_hash_fixed(item):
        """Fixed version of item_hash."""
        dhash = hashlib.md5()
        if isinstance(item, dict):
            item = {k: item_hash_fixed(v) for k, v in item.items()}
        if isinstance(item, list):
            sorted_hashes = sorted([item_hash_fixed(i) for i in item])
            item = sorted_hashes  # This is what it should be
        encoded = json.dumps(item, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()
    
    simple_list = [1, 2, 3]
    print(f"Fixed hash for {simple_list}: {item_hash_fixed(simple_list)}")
    
    # Test 3: Complex nested structure with list
    nested = {"a": [1, 2], "b": {"c": [3, 4]}}
    print(f"\nTesting nested structure: {nested}")
    try:
        result = item_hash(nested)
        print(f"Hash result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        
    # Test 4: Show that lists cause json.dumps to fail
    print("\n--- Direct demonstration of the bug ---")
    test_list = [1, 2, 3]
    print(f"Original list: {test_list}")
    
    # Simulate what happens in item_hash
    processed = [str(i) for i in test_list].sort()
    print(f"After [].sort(): {processed}")  # This will be None!
    
    try:
        json.dumps(processed)
    except TypeError as e:
        print(f"json.dumps fails with: {e}")
        print("This is because .sort() returns None, not the sorted list!")


if __name__ == "__main__":
    test_item_hash_list_bug()