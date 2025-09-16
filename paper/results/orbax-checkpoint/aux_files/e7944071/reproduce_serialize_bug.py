#!/usr/bin/env python3
"""Minimal reproduction of serialize_tree bug with empty nested dictionaries."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint.tree as tree

# Bug 1: serialize_tree fails on trees with empty nested dictionaries
print("Bug 1: serialize_tree with empty nested dict")
print("=" * 50)

test_tree = {'a': {}}
print(f"Input tree: {test_tree}")

try:
    serialized = tree.serialize_tree(test_tree, keep_empty_nodes=False)
    print(f"Serialized: {serialized}")
    
    deserialized = tree.deserialize_tree(serialized, test_tree, keep_empty_nodes=False)
    print(f"Deserialized: {deserialized}")
    
    if deserialized == test_tree:
        print("✓ Round-trip successful")
    else:
        print(f"✗ Round-trip failed: {test_tree} != {deserialized}")
except Exception as e:
    print(f"✗ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")

print("\nExplanation:")
print("The function fails when the tree contains empty nested dictionaries.")
print("The error 'Unable to uniquely reconstruct tree from empty flattened list'")
print("occurs because empty dicts are filtered out, leaving an ambiguous structure.")

# Test with keep_empty_nodes=True
print("\n" + "=" * 50)
print("Testing with keep_empty_nodes=True:")
try:
    serialized = tree.serialize_tree(test_tree, keep_empty_nodes=True)
    print(f"Serialized: {serialized}")
    
    deserialized = tree.deserialize_tree(serialized, test_tree, keep_empty_nodes=True)
    print(f"Deserialized: {deserialized}")
    
    if deserialized == test_tree:
        print("✓ Round-trip successful with keep_empty_nodes=True")
    else:
        print(f"✗ Round-trip failed")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Additional test cases
print("\n" + "=" * 50)
print("Additional problematic structures:")

test_cases = [
    {'a': {}, 'b': 1},  # Mixed empty and non-empty
    {'a': {'b': {}}},   # Nested empty dict
    {'a': {'b': {'c': {}}}},  # Deeply nested empty
]

for test_tree in test_cases:
    print(f"\nTesting: {test_tree}")
    try:
        serialized = tree.serialize_tree(test_tree, keep_empty_nodes=False)
        deserialized = tree.deserialize_tree(serialized, test_tree, keep_empty_nodes=False)
        print(f"  ✓ Success: {deserialized}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")