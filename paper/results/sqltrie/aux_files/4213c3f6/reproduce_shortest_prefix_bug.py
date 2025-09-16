import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import SQLiteTrie

trie = SQLiteTrie()
trie[()] = b''
trie[('0',)] = b''

result = trie.shortest_prefix(('0',))
print(f"shortest_prefix(('0',)) returned: {result}")
print(f"Expected: ((), b'')")
print(f"Actual: {result}")

if result[0] != ():
    print("\nBUG CONFIRMED: shortest_prefix returns ('0',) instead of () which is shorter")