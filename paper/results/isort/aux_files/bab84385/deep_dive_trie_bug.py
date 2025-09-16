import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.utils
from pathlib import Path

# Let's trace through the Trie implementation step by step
trie = isort.utils.Trie()

print("=== Inserting configs ===")
# Insert /0 first
print("Inserting /0...")
resolved_path_1 = Path('/0').parent.resolve().parts
print(f"  Resolved parts for /0's parent: {resolved_path_1}")
trie.insert('/0', {'id': 'config1'})

# Insert /00 second  
print("Inserting /00...")
resolved_path_2 = Path('/00').parent.resolve().parts  
print(f"  Resolved parts for /00's parent: {resolved_path_2}")
trie.insert('/00', {'id': 'config2'})

print("\n=== Understanding the Trie structure ===")
print(f"Root config info: {trie.root.config_info}")
print(f"Root nodes keys: {list(trie.root.nodes.keys())}")

# The parent of both /0 and /00 is /, which resolves to ('/',)
# So both configs are being stored at the same node!
if '/' in trie.root.nodes:
    node = trie.root.nodes['/']
    print(f"Node at '/' config info: {node.config_info}")
    print(f"Node at '/' has subnodes: {list(node.nodes.keys())}")

print("\n=== Searching for /test.py ===")
search_parts = Path('/test.py').resolve().parts
print(f"Search path resolved parts: {search_parts}")

# Manually trace the search
temp = trie.root
last_stored_config = ("", {})
print(f"Starting at root, config_info: {temp.config_info}")

for i, path in enumerate(search_parts):
    print(f"\nStep {i+1}: Looking for '{path}'")
    
    if temp.config_info[0]:
        print(f"  Current node has config: {temp.config_info}")
        last_stored_config = temp.config_info
    
    if path not in temp.nodes:
        print(f"  '{path}' not found in nodes, breaking")
        break
    
    temp = temp.nodes[path]
    print(f"  Moved to node '{path}', config_info: {temp.config_info}")

print(f"\nFinal last_stored_config: {last_stored_config}")

# The issue is that when both configs have the same parent path,
# the second insert overwrites the first one's config_info!