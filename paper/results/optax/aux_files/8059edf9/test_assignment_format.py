#!/usr/bin/env python3
"""Test the format of assignments returned by Hungarian algorithms."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax
import jax.numpy as jnp
from optax import assignment
import numpy as np

# Disable JIT
jax.config.update('jax_disable_jit', True)


def analyze_assignment_format():
    """Analyze what format the assignments are returned in."""
    print("=== Analyzing assignment format ===")
    print("\nBased on documentation:")
    print("- Returns (i, j) where i is row indices and j is column indices")
    print("- The cost of the assignment is cost_matrix[i, j].sum()")
    print("\nLet's verify this...\n")
    
    # Test case 1: More rows than columns
    print("Test 1: More rows than columns (4x3)")
    cost = jnp.array([
        [8, 4, 7],
        [5, 2, 3],
        [9, 6, 7],
        [9, 4, 8],
    ], dtype=jnp.float32)
    
    print(f"Cost matrix:\n{cost}")
    
    i1, j1 = assignment.hungarian_algorithm(cost)
    i2, j2 = assignment.base_hungarian_algorithm(cost)
    
    print(f"\nhungarian_algorithm returns:")
    print(f"  i (row indices): {i1.tolist()}")
    print(f"  j (col indices): {j1.tolist()}")
    print(f"  Assignments: {[(r, c) for r, c in zip(i1, j1)]}")
    print(f"  Total cost: {cost[i1, j1].sum()}")
    
    print(f"\nbase_hungarian_algorithm returns:")
    print(f"  i (row indices): {i2.tolist()}")
    print(f"  j (col indices): {j2.tolist()}")
    print(f"  Assignments: {[(r, c) for r, c in zip(i2, j2)]}")
    print(f"  Total cost: {cost[i2, j2].sum()}")
    
    # Check format expectations
    print(f"\nFormat analysis:")
    print(f"  Expected # assignments: min(4,3) = 3")
    print(f"  Actual # assignments (hungarian): {len(i1)}")
    print(f"  Actual # assignments (base): {len(i2)}")
    
    # Does hungarian_algorithm always return sorted indices for square matrices?
    print("\n" + "="*50)
    print("Test 2: Square matrix (3x3)")
    cost_sq = jnp.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ], dtype=jnp.float32)
    
    i1_sq, j1_sq = assignment.hungarian_algorithm(cost_sq)
    i2_sq, j2_sq = assignment.base_hungarian_algorithm(cost_sq)
    
    print(f"hungarian: i={i1_sq.tolist()}, j={j1_sq.tolist()}")
    print(f"base: i={i2_sq.tolist()}, j={j2_sq.tolist()}")
    
    # Test the documented behavior difference
    print("\n" + "="*50)
    print("Testing implementation differences mentioned in docstrings...")
    print("\nFrom base_hungarian_algorithm docstring (line 131-132):")
    print("  if transpose:")
    print("    return col4row[i], i  # Returns sorted row indices")
    print("  else:")
    print("    return jnp.arange(cost_matrix.shape[0]), col4row")
    print("\nThis means base_hungarian returns ALL row indices when rows <= cols")
    
    # Let's verify this
    print("\nVerification with 2x3 matrix:")
    cost_2x3 = jnp.array([[1, 2, 3], [4, 5, 6]], dtype=jnp.float32)
    i_base, j_base = assignment.base_hungarian_algorithm(cost_2x3)
    print(f"  base result: i={i_base.tolist()}, j={j_base.tolist()}")
    print(f"  Are row indices [0, 1]? {i_base.tolist() == [0, 1]}")
    
    print("\nFrom hungarian_algorithm docstring (line 530-532):")
    print("  if transpose:")
    print("    return indices, parent")
    print("  return parent, indices")
    print("\nSo the format differs based on whether the matrix was transposed internally")


def test_format_discrepancy():
    """Test if there's a format discrepancy between the two implementations."""
    print("\n" + "="*60)
    print("=== Testing potential format discrepancy ===\n")
    
    # When rows < cols, base_hungarian returns ALL row indices 0..n-1
    # But hungarian might not
    
    cost_2x5 = jnp.array([
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10]
    ], dtype=jnp.float32)
    
    print(f"Test matrix (2x5):\n{cost_2x5}")
    
    i1, j1 = assignment.hungarian_algorithm(cost_2x5)
    i2, j2 = assignment.base_hungarian_algorithm(cost_2x5)
    
    print(f"\nhungarian_algorithm:")
    print(f"  i={i1.tolist()}, j={j1.tolist()}")
    print(f"  Format: Are rows sequential? {sorted(i1.tolist()) == list(range(len(i1)))}")
    
    print(f"\nbase_hungarian_algorithm:")
    print(f"  i={i2.tolist()}, j={j2.tolist()}")
    print(f"  Format: Are rows [0, 1]? {i2.tolist() == [0, 1]}")
    
    # The key question: Do both implementations guarantee the same format?
    print(f"\nDo the formats match? {(i1.tolist(), j1.tolist()) == (i2.tolist(), j2.tolist())}")
    
    if i1.tolist() != i2.tolist() or j1.tolist() != j2.tolist():
        print("\nFORMAT DISCREPANCY FOUND!")
        print("The two implementations return indices in different orders.")
        print("This is not necessarily a bug if both achieve optimal cost,")
        print("but it could cause issues for code expecting a specific format.")


def test_documentation_claims():
    """Test specific claims from the documentation."""
    print("\n" + "="*60)
    print("=== Testing documentation claims ===\n")
    
    # From the examples in docstring
    cost1 = jnp.array([
        [8, 4, 7],
        [5, 2, 3],
        [9, 6, 7],
        [9, 4, 8],
    ])
    
    print("Example 1 from docstring:")
    print(f"Cost matrix shape: {cost1.shape}")
    
    i, j = assignment.hungarian_algorithm(cost1)
    print(f"hungarian_algorithm result:")
    print(f"  i: {i.tolist()}")
    print(f"  j: {j.tolist()}")
    print(f"  cost: {cost1[i, j].sum()}")
    
    # The docstring example shows specific expected output
    # Let's check if we get exactly that
    print(f"\nDocstring claims i=[0,1,3], j=[0,2,1]")
    print(f"Actual result matches? i={i.tolist() == [0,1,3]}, j={j.tolist() == [0,2,1]}")
    
    # For base_hungarian_algorithm
    i2, j2 = assignment.base_hungarian_algorithm(cost1)
    print(f"\nbase_hungarian_algorithm result:")
    print(f"  i: {i2.tolist()}")
    print(f"  j: {j2.tolist()}")
    print(f"  cost: {cost1[i2, j2].sum()}")


if __name__ == "__main__":
    analyze_assignment_format()
    test_format_discrepancy()
    test_documentation_claims()