import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie.pygtrie import PyGTrie

# Bug 2: longest_prefix returns incorrect value format
trie = PyGTrie()
trie[()] = b'root_value'  # Empty tuple as key
trie[('a',)] = b'a_value'
trie[('a', 'b')] = b'ab_value'

# Test 1: longest_prefix for empty key
result = trie.longest_prefix(())
print(f"longest_prefix(()) = {result}")
print(f"Type: {type(result)}")

# According to the interface, this should return just the key, not (key, value)
# The expected result should be () (the empty tuple key)
# But we're getting something else

# Test 2: longest_prefix for a key with value
result2 = trie.longest_prefix(('a', 'b', 'c'))
print(f"\nlongest_prefix(('a', 'b', 'c')) = {result2}")
print(f"Type: {type(result2)}")

# This should return ('a', 'b') since that's the longest prefix with a value
# Let's check what we actually get

# Test 3: Check the underlying pygtrie behavior
import pygtrie
base_trie = pygtrie.Trie()
base_trie[()] = b'root'
base_trie[('a', 'b')] = b'ab'

base_result = base_trie.longest_prefix(('a', 'b', 'c'))
print(f"\nDirect pygtrie longest_prefix: {base_result}")
print(f"Type: {type(base_result)}")