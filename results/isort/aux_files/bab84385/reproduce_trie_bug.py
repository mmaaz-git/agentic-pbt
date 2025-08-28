import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.utils
from pathlib import Path

# Minimal reproduction based on the failing test
trie = isort.utils.Trie()

# Insert two configs
config1 = ('/0', {})
config2 = ('/00', {})

trie.insert(config1[0], config1[1])
trie.insert(config2[0], config2[1])

# Search for a file in the root directory
search_path = '/test.py'
found_file, found_data = trie.search(search_path)

print(f"Configs inserted:")
print(f"  Config 1: {config1[0]} -> {config1[1]}")
print(f"  Config 2: {config2[0]} -> {config2[1]}")
print(f"\nSearching for: {search_path}")
print(f"Found: {found_file}")
print(f"Expected: /0 or empty (since /0 and /00 are files, not directories)")

# Let's understand what's happening
print("\n--- Detailed Analysis ---")
print(f"Config 1 parent: {Path(config1[0]).parent}")
print(f"Config 2 parent: {Path(config2[0]).parent}")
print(f"Search file parent: {Path(search_path).parent}")

print("\n--- Path resolution ---")
print(f"Config 1 parent resolved: {Path(config1[0]).parent.resolve()}")
print(f"Config 2 parent resolved: {Path(config2[0]).parent.resolve()}")
print(f"Search path resolved: {Path(search_path).resolve()}")

# Test with actual directories
print("\n--- Testing with actual directory configs ---")
trie2 = isort.utils.Trie()
trie2.insert('/dir1/config.ini', {'setting': 'value1'})
trie2.insert('/dir1/subdir/config.ini', {'setting': 'value2'})

search1 = '/dir1/file.py'
search2 = '/dir1/subdir/file.py'

found1 = trie2.search(search1)
found2 = trie2.search(search2)

print(f"Search {search1}: Found {found1[0]}")
print(f"Search {search2}: Found {found2[0]}")