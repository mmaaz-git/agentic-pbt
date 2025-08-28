import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import SQLiteTrie


print("Testing shortest_prefix behavior more thoroughly...")
trie = SQLiteTrie()

trie[()] = b'root'
trie[('a',)] = b'a'
trie[('a', 'b')] = b'ab'
trie[('a', 'b', 'c')] = b'abc'

test_keys = [
    ('a', 'b', 'c', 'd'),
    ('a', 'b', 'c'),
    ('a', 'b'),
    ('a',),
    ('x',),
]

for key in test_keys:
    result = trie.shortest_prefix(key)
    print(f"shortest_prefix({key}) = {result}")
    
    all_prefixes = list(trie.prefixes(key))
    if all_prefixes:
        expected_shortest = min(all_prefixes, key=lambda x: len(x[0]))
        if result != expected_shortest:
            print(f"  ERROR: Expected {expected_shortest} but got {result}")

print("\n" + "="*50)
print("Checking the specific bug case:")
trie2 = SQLiteTrie()
trie2[()] = b'root_value'
trie2[('0',)] = b'zero_value'

print(f"Set () = b'root_value'")
print(f"Set ('0',) = b'zero_value'")

result = trie2.shortest_prefix(('0',))
all_prefixes = list(trie2.prefixes(('0',)))
print(f"\nAll prefixes of ('0',): {all_prefixes}")
print(f"shortest_prefix(('0',)) returned: {result}")

if all_prefixes:
    expected = min(all_prefixes, key=lambda x: len(x[0]))
    print(f"Expected shortest (by length): {expected}")
    if result != expected:
        print("\n*** BUG CONFIRMED: shortest_prefix doesn't return the shortest prefix! ***")