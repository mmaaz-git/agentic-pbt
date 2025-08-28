#!/usr/bin/env python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import JSONTrie
from sqltrie.pygtrie import PyGTrie

class ConcreteJSONTrie(JSONTrie):
    def __init__(self):
        self._inner_trie = PyGTrie()
    
    @property
    def _trie(self):
        return self._inner_trie
    
    @classmethod
    def open(cls, path):
        raise NotImplementedError

# Test case 1: shortest_prefix bug
print("Testing shortest_prefix bug...")
trie = ConcreteJSONTrie()

# Create a base key and an extended key
base_key = ('a',)
extended_key = ('a', 'b')

# Set values for both
trie[base_key] = "base"
trie[extended_key] = "extended"

# Query with the extended key
result = trie.shortest_prefix(extended_key)

if result is not None:
    returned_key, returned_value = result
    print(f"Query key: {extended_key}")
    print(f"Expected shortest prefix: {base_key}")
    print(f"Actual returned key: {returned_key}")
    print(f"Returned value: {returned_value}")
    
    if returned_key == extended_key:
        print("BUG FOUND: shortest_prefix returns the query key instead of the actual shortest prefix!")
    else:
        print("Test passed")
        
print("\n" + "="*50 + "\n")

# Test case 2: Query with longer key than stored
print("Testing shortest_prefix with query longer than stored keys...")
trie2 = ConcreteJSONTrie()

short_key = ('x',)
query_key = ('x', 'y', 'z')

trie2[short_key] = "short"

result2 = trie2.shortest_prefix(query_key)

if result2 is not None:
    returned_key2, returned_value2 = result2
    print(f"Query key: {query_key}")
    print(f"Expected shortest prefix: {short_key}")
    print(f"Actual returned key: {returned_key2}")
    print(f"Returned value: {returned_value2}")
    
    if returned_key2 == query_key:
        print("BUG CONFIRMED: shortest_prefix incorrectly returns the query key!")
    else:
        print("Test passed")