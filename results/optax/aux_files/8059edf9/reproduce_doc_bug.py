#!/usr/bin/env python3
"""Minimal reproduction of documentation bug in optax.assignment.hungarian_algorithm."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax.numpy as jnp
from optax import assignment

# Example from the docstring of hungarian_algorithm (lines 415-424)
cost = jnp.array([
    [8, 4, 7],
    [5, 2, 3],
    [9, 6, 7],
    [9, 4, 8],
])

print("Testing example from hungarian_algorithm docstring...")
print(f"Cost matrix:\n{cost}\n")

# Run the algorithm
i, j = assignment.hungarian_algorithm(cost)

print(f"Actual output:")
print(f"  i: {i.tolist()}")
print(f"  j: {j.tolist()}")
print(f"  cost: {cost[i, j].sum()}")

print(f"\nExpected output (from docstring lines 422-424):")
print(f"  i: [0, 1, 3]")
print(f"  j: [0, 2, 1]")
print(f"  cost: 15")

print(f"\nDoes actual match expected?")
print(f"  i matches: {i.tolist() == [0, 1, 3]}")
print(f"  j matches: {j.tolist() == [0, 2, 1]}")
print(f"  cost matches: {cost[i, j].sum() == 15}")

# Let's also check base_hungarian_algorithm
print("\n" + "="*50)
print("For comparison, base_hungarian_algorithm output:")
i2, j2 = assignment.base_hungarian_algorithm(cost)
print(f"  i: {i2.tolist()}")
print(f"  j: {j2.tolist()}")
print(f"  cost: {cost[i2, j2].sum()}")

# Second example from hungarian_algorithm docstring
print("\n" + "="*50)
print("Testing second example from hungarian_algorithm docstring...")
cost2 = jnp.array([
    [90, 80, 75, 70],
    [35, 85, 55, 65],
    [125, 95, 90, 95],
    [45, 110, 95, 115],
    [50, 100, 90, 100],
])

print(f"Cost matrix shape: {cost2.shape}\n")

i, j = assignment.hungarian_algorithm(cost2)
print(f"Actual output:")
print(f"  cost: {cost2[i, j].sum()}")

print(f"\nExpected output (from docstring line 435):")
print(f"  cost: 265")

print(f"\nCost matches: {cost2[i, j].sum() == 265}")