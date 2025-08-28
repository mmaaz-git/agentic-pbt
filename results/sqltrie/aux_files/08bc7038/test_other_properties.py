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

# Test JSON round-trip
print("Testing JSON round-trip...")
from sqltrie.serialized import json_dumps, json_loads

test_values = [
    None,
    True,
    42,
    3.14,
    "hello",
    [1, 2, 3],
    {"key": "value"}
]

for value in test_values:
    serialized = json_dumps(value)
    deserialized = json_loads(serialized)
    assert deserialized == value, f"Round-trip failed for {value}"
print("JSON round-trip: PASSED ✅")

# Test JSONTrie set/get
print("\nTesting JSONTrie set/get...")
trie = ConcreteJSONTrie()
test_data = [
    (('key1',), "value1"),
    (('key2',), None),
    (('key3',), [1, 2, 3]),
    (('key4',), {"nested": "dict"})
]

for key, value in test_data:
    trie[key] = value
    retrieved = trie[key]
    assert retrieved == value, f"Set/get failed for {key}: {value}"
print("JSONTrie set/get: PASSED ✅")

# Test longest_prefix
print("\nTesting longest_prefix...")
trie2 = ConcreteJSONTrie()
trie2[('a',)] = "short"
trie2[('a', 'b')] = "medium"  
trie2[('a', 'b', 'c')] = "long"

result = trie2.longest_prefix(('a', 'b', 'c', 'd'))
if result:
    key, value = result
    assert key == ('a', 'b', 'c'), f"Expected ('a', 'b', 'c'), got {key}"
    assert value == "long", f"Expected 'long', got {value}"
    print("longest_prefix: PASSED ✅")
else:
    print("longest_prefix: FAILED - returned None")

# Test prefixes iteration
print("\nTesting prefixes iteration...")
trie3 = ConcreteJSONTrie()
trie3[('x',)] = 1
trie3[('x', 'y')] = 2
trie3[('x', 'y', 'z')] = 3

prefixes = list(trie3.prefixes(('x', 'y', 'z', 'w')))
expected = [(('x',), 1), (('x', 'y'), 2), (('x', 'y', 'z'), 3)]
assert len(prefixes) == len(expected), f"Expected {len(expected)} prefixes, got {len(prefixes)}"
for prefix in expected:
    assert prefix in prefixes, f"Missing prefix: {prefix}"
print("prefixes iteration: PASSED ✅")