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

trie = ConcreteJSONTrie()

trie[('a',)] = "base"
trie[('a', 'b')] = "extended"

result = trie.shortest_prefix(('a', 'b'))
returned_key, returned_value = result

print(f"Expected key: ('a',)")
print(f"Actual key: {returned_key}")
print(f"Bug: Returns {returned_key} instead of ('a',)")