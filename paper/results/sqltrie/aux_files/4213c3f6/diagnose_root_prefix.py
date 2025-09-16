import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import SQLiteTrie

print("Testing if root node () is properly handled as a prefix...")

trie = SQLiteTrie()
trie[()] = b'root_value'
trie[('a',)] = b'a_value'
trie[('a', 'b')] = b'ab_value'

print("\nTrie contents:")
for k, v in trie.items():
    print(f"  {k} -> {v}")

test_keys = [
    (),
    ('a',),
    ('a', 'b'),
    ('a', 'b', 'c'),
    ('x',),
]

print("\nTesting prefixes():")
for key in test_keys:
    prefixes = list(trie.prefixes(key))
    print(f"  prefixes({key}) = {prefixes}")
    
    if key != () and trie.get(()) is not None:
        if not any(p[0] == () for p in prefixes):
            print(f"    WARNING: Root () has a value but is not in prefixes!")

print("\nDirect test:")
print(f"  trie[()] exists: {() in trie}")
print(f"  trie[()] value: {trie[()]}")
print(f"  prefixes(('a',)): {list(trie.prefixes(('a',)))}")

if () in trie and () not in [p[0] for p in trie.prefixes(('a',))]:
    print("\n*** BUG CONFIRMED: Root node with value is not returned by prefixes() ***")