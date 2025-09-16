import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from test_pygtrie_properties import trie_with_items, trie_keys

@given(trie_with_items(), trie_keys())
def test_longest_prefix_fixed(trie_items, key):
    """Property: longest_prefix should return a TrieStep (key, value) tuple."""
    trie, items = trie_items
    
    result = trie.longest_prefix(key)
    
    if result is not None:
        # Result should be a tuple of (key, value)
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        longest_key, longest_value = result
        
        # The key should be a prefix of the input key
        assert key[:len(longest_key)] == longest_key
        # It should exist in the trie
        assert longest_key in trie
        assert trie[longest_key] == longest_value
        
        # No longer prefix should exist
        for stored_key in items:
            if len(stored_key) > len(longest_key) and key[:len(stored_key)] == stored_key:
                assert False, f"Found longer prefix {stored_key}"

if __name__ == "__main__":
    test_longest_prefix_fixed()
    print("Test passed!")