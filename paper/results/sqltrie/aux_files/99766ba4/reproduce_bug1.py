import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie.pygtrie import PyGTrie

# Bug 1: items() with non-existent prefix raises KeyError
trie = PyGTrie()
# Empty trie, no items

try:
    # This should return an empty iterator, not raise KeyError
    list(trie.items(prefix=('nonexistent',)))
    print("No error - expected behavior")
except KeyError as e:
    print(f"BUG: KeyError raised: {e}")
    print("Expected: Empty iterator should be returned")

# Also test with a trie that has some items
trie2 = PyGTrie()
trie2[('a', 'b')] = b'value1'
trie2[('a', 'c')] = b'value2'

try:
    # Prefix that doesn't exist should return empty iterator
    result = list(trie2.items(prefix=('x', 'y')))
    print(f"Result for non-existent prefix: {result}")
    print("Expected: Empty list")
except KeyError as e:
    print(f"BUG: KeyError raised: {e}")
    print("Expected: Empty iterator should be returned")