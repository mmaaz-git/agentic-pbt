#!/usr/bin/env python3
"""Check what PyTree means in JAX context."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import jax

# Test what JAX considers a PyTree
test_values = [
    42,                      # scalar
    [1, 2, 3],              # list
    {'a': 1},               # dict
    (1, 2),                 # tuple
    {'a': {}, 'b': 1},      # dict with empty nested dict
]

print("JAX PyTree behavior:")
print("=" * 50)

for value in test_values:
    print(f"\nValue: {value}")
    print(f"Type: {type(value).__name__}")
    
    # Flatten and unflatten
    flat, treedef = jax.tree_util.tree_flatten(value)
    print(f"Flattened: {flat}")
    print(f"Tree structure: {treedef}")
    
    # Reconstruct
    reconstructed = jax.tree_util.tree_unflatten(treedef, flat)
    print(f"Reconstructed: {reconstructed}")
    print(f"Round-trip success: {reconstructed == value}")

# Check if scalars are valid PyTrees
print("\n" + "=" * 50)
print("Are scalars valid PyTrees in JAX?")
scalar = 42
flat, treedef = jax.tree_util.tree_flatten(scalar)
print(f"Scalar {scalar} flattened to: {flat}")
print(f"This shows scalars ARE valid PyTrees (leaf nodes)")

# Test tree_map with scalars
print("\n" + "=" * 50)
print("JAX tree_map with scalars:")
result = jax.tree_map(lambda x: x * 2, 42)
print(f"tree_map(lambda x: x*2, 42) = {result}")

result = jax.tree_map(lambda x: x * 2, [1, 2, 3])
print(f"tree_map(lambda x: x*2, [1,2,3]) = {result}")