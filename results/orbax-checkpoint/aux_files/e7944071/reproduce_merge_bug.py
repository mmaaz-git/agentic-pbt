#!/usr/bin/env python3
"""Minimal reproduction of merge_trees bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import orbax.checkpoint.transform_utils as transform_utils

print("Bug 2: merge_trees with scalar inputs")
print("=" * 50)

# Bug 2.1: Single scalar returns empty dict instead of scalar
print("\nTest 1: merge_trees with single scalar")
scalar = 42
result = transform_utils.merge_trees(scalar)
print(f"Input: {scalar}")
print(f"Result: {result}")
print(f"Expected: {scalar}")
print(f"✗ BUG: Returns {result} instead of {scalar}")

# Bug 2.2: Merging scalar with empty dict
print("\nTest 2: merge_trees(scalar, {})")
scalar = 100
result = transform_utils.merge_trees(scalar, {})
print(f"Input: merge_trees({scalar}, {{}})")
print(f"Result: {result}")
print(f"Expected: {scalar}")
print(f"✗ BUG: Returns {result} instead of {scalar}")

# Bug 2.3: Type conflict between scalar and dict
print("\nTest 3: merge_trees with type conflict")
tree1 = {'a': 0}
tree2 = {'a': {'b': 1}}
try:
    result = transform_utils.merge_trees(tree1, tree2)
    print(f"Input: tree1={tree1}, tree2={tree2}")
    print(f"Result: {result}")
except TypeError as e:
    print(f"Input: tree1={tree1}, tree2={tree2}")
    print(f"✗ TypeError: {e}")
    print("BUG: Cannot handle type conflicts between scalar and dict values")

# Additional tests
print("\n" + "=" * 50)
print("Additional edge cases:")

# Test with lists
print("\nTest 4: merge_trees with lists")
list_input = [1, 2, 3]
result = transform_utils.merge_trees(list_input)
print(f"Input: {list_input}")
print(f"Result: {result}")
if result != list_input:
    print(f"✗ BUG: Lists are not handled correctly")

# Test intersect_trees with scalars
print("\nTest 5: intersect_trees with scalars")
scalar = 42
result = transform_utils.intersect_trees(scalar, scalar)
print(f"Input: intersect_trees({scalar}, {scalar})")
print(f"Result: {result}")
print(f"Expected: {scalar}")
if result != scalar:
    print(f"✗ BUG: Returns {result} instead of {scalar}")

# Verify the implementation assumes dict input
print("\n" + "=" * 50)
print("Root cause analysis:")
print("The functions use to_flat_dict which likely assumes dict input.")
print("Non-dict inputs are being incorrectly handled.")