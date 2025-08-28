#!/usr/bin/env python3
"""Minimal reproductions of the discovered bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint.tree as tree_module

print("Testing serialize_tree bugs with empty containers...")
print("=" * 60)

# Bug 1: AssertionError with [[[], 0]]
print("\nBug 1: Nested list with empty list and value")
try:
    tree1 = [[[], 0]]
    print(f"Input: {tree1}")
    result = tree_module.serialize_tree(tree1)
    print(f"Success: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Bug 2: ValueError with [[[]]]
print("\nBug 2: Deeply nested empty list")
try:
    tree2 = [[[]]]
    print(f"Input: {tree2}")
    result = tree_module.serialize_tree(tree2)
    print(f"Success: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Bug 3: ValueError with {'a': {}} when keep_empty_nodes=False
print("\nBug 3: Dict with empty dict value")
try:
    tree3 = {'a': {}}
    print(f"Input: {tree3}")
    result = tree_module.serialize_tree(tree3, keep_empty_nodes=False)
    print(f"Success: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Additional test - what about with keep_empty_nodes=True?
print("\nBug 3b: Same tree with keep_empty_nodes=True")
try:
    tree3 = {'a': {}}
    print(f"Input: {tree3}")
    result = tree_module.serialize_tree(tree3, keep_empty_nodes=True)
    print(f"Success (keep_empty_nodes=True): {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# More edge cases
print("\nAdditional edge case: [[], [1]]")
try:
    tree4 = [[], [1]]
    print(f"Input: {tree4}")
    result = tree_module.serialize_tree(tree4)
    print(f"Success: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\nAdditional edge case: [[1], []]")
try:
    tree5 = [[1], []]
    print(f"Input: {tree5}")
    result = tree_module.serialize_tree(tree5)
    print(f"Success: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Summary:")
print("serialize_tree has issues with empty containers in lists")
print("The function fails when:")
print("1. A list contains an empty container followed by a value")
print("2. A list contains only empty containers")
print("3. A dict has empty dict values (with keep_empty_nodes=False)")