#!/usr/bin/env python3
"""Test to expose the bug in item_hash function with lists."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.utils import item_hash
from hypothesis import given, strategies as st


# Test that exposes the bug in item_hash for lists
@given(st.lists(st.integers(), min_size=1, max_size=5))
def test_item_hash_list_bug(lst):
    """Test item_hash on lists - this should fail due to the .sort() bug."""
    # This should compute a hash, but will fail because .sort() returns None
    hash_result = item_hash(lst)
    
    # The hash should be a string
    assert isinstance(hash_result, str)
    assert len(hash_result) == 32  # MD5 hash is 32 hex chars
    
    # Also test that permutations of the same list have the same hash
    # (since it's supposed to sort the list)
    if len(lst) > 1:
        import random
        lst_copy = lst.copy()
        random.shuffle(lst_copy)
        hash_shuffled = item_hash(lst_copy)
        assert hash_result == hash_shuffled, f"Different hashes for same list contents: {lst} vs {lst_copy}"


if __name__ == "__main__":
    # Try a simple test case that will expose the bug
    try:
        result = item_hash([3, 1, 2])
        print(f"Hash result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        print("Bug confirmed: item_hash fails on lists due to .sort() returning None")