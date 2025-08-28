#!/usr/bin/env python3
"""Property test that reveals the item_hash bug for lists."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.utils import item_hash
from hypothesis import given, strategies as st
import hashlib


@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_item_hash_list_produces_different_hashes(lst):
    """Different lists should produce different hashes (except in rare collisions)."""
    hash1 = item_hash(lst)
    
    # Create a different list by appending an element
    different_list = lst + [999999]
    hash2 = item_hash(different_list)
    
    # These should be different (unless we have a hash collision, which is very rare)
    # But due to the bug, both will hash to the MD5 of "null"
    assert hash1 != hash2, f"Different lists produced same hash: {lst} and {different_list} both hash to {hash1}"


@given(st.lists(st.integers(), min_size=1))
def test_item_hash_not_null_hash(lst):
    """Lists should not all hash to the MD5 of 'null'."""
    hash_result = item_hash(lst)
    null_hash = hashlib.md5(b'null').hexdigest()
    
    # Due to the bug, all lists hash to the MD5 of "null"
    assert hash_result != null_hash, f"List {lst} incorrectly hashes to MD5('null'): {hash_result}"


if __name__ == "__main__":
    # Direct demonstration of the bug
    print("Demonstrating the item_hash bug:")
    
    list1 = [1, 2, 3]
    list2 = [4, 5, 6]
    list3 = ["a", "b", "c"]
    
    hash1 = item_hash(list1)
    hash2 = item_hash(list2)
    hash3 = item_hash(list3)
    
    null_hash = hashlib.md5(b'null').hexdigest()
    
    print(f"Hash of [1, 2, 3]: {hash1}")
    print(f"Hash of [4, 5, 6]: {hash2}")
    print(f"Hash of ['a', 'b', 'c']: {hash3}")
    print(f"MD5 hash of 'null': {null_hash}")
    
    if hash1 == hash2 == hash3 == null_hash:
        print("\nBUG CONFIRMED: All lists hash to the same value (MD5 of 'null')")
        print("This is because line 32 uses .sort() which returns None")