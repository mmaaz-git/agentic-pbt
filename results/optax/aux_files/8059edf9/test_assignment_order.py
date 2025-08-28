#!/usr/bin/env python3
"""Test if assignment order differences between implementations cause issues."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax
import jax.numpy as jnp
from optax import assignment
import numpy as np

# Disable JIT to avoid timing issues  
jax.config.update('jax_disable_jit', True)


def test_rectangular_matrices_costs():
    """Test if costs match even when assignment order differs."""
    print("=== Testing rectangular matrices for cost consistency ===")
    
    np.random.seed(42)
    
    found_difference = False
    
    for _ in range(100):
        # Generate random rectangular matrices
        rows = np.random.randint(1, 20)
        cols = np.random.randint(1, 20)
        
        if rows == cols:
            continue  # Skip square matrices
        
        cost_matrix = jnp.array(np.random.randn(rows, cols), dtype=jnp.float32)
        
        i1, j1 = assignment.hungarian_algorithm(cost_matrix)
        i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
        
        cost1 = cost_matrix[i1, j1].sum()
        cost2 = cost_matrix[i2, j2].sum()
        
        if not jnp.allclose(cost1, cost2, rtol=1e-5, atol=1e-8):
            print(f"\nFound cost difference!")
            print(f"Shape: {cost_matrix.shape}")
            print(f"hungarian cost: {cost1}")
            print(f"base cost: {cost2}")
            print(f"Difference: {abs(cost1 - cost2)}")
            print(f"Cost matrix:\n{cost_matrix}")
            found_difference = True
            break
    
    if not found_difference:
        print("No cost differences found in 100 random tests.")


def test_specific_rectangular_case():
    """Test a specific case where order might matter."""
    print("\n=== Testing specific rectangular case ===")
    
    # Create a matrix where different assignments have different costs
    cost_matrix = jnp.array([[1.0, 10.0],
                              [2.0, 20.0],
                              [3.0, 30.0]], dtype=jnp.float32)
    
    print(f"Cost matrix:\n{cost_matrix}")
    
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
    
    cost1 = cost_matrix[i1, j1].sum()
    cost2 = cost_matrix[i2, j2].sum()
    
    print(f"\nhungarian_algorithm:")
    print(f"  Assignments: rows {i1.tolist()} -> cols {j1.tolist()}")
    print(f"  Cost: {cost1}")
    print(f"  Assignment details:")
    for r, c in zip(i1, j1):
        print(f"    Row {r} -> Col {c}: cost = {cost_matrix[r, c]}")
    
    print(f"\nbase_hungarian_algorithm:")
    print(f"  Assignments: rows {i2.tolist()} -> cols {j2.tolist()}")
    print(f"  Cost: {cost2}")
    print(f"  Assignment details:")
    for r, c in zip(i2, j2):
        print(f"    Row {r} -> Col {c}: cost = {cost_matrix[r, c]}")
    
    if not jnp.allclose(cost1, cost2):
        print(f"\nERROR: Costs differ by {abs(cost1 - cost2)}")


def test_edge_case_single_element():
    """Test edge cases with very small matrices."""
    print("\n=== Testing edge cases ===")
    
    # Single element
    cost_matrix = jnp.array([[5.0]])
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
    print(f"Single element (1x1):")
    print(f"  hungarian: i={i1.tolist()}, j={j1.tolist()}")
    print(f"  base: i={i2.tolist()}, j={j2.tolist()}")
    
    # Empty matrices
    for shape in [(0, 0), (0, 5), (5, 0)]:
        cost_matrix = jnp.zeros(shape)
        i1, j1 = assignment.hungarian_algorithm(cost_matrix)
        i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
        print(f"\nEmpty matrix {shape}:")
        print(f"  hungarian: i={i1.tolist()}, j={j1.tolist()}")
        print(f"  base: i={i2.tolist()}, j={j2.tolist()}")


def test_assignment_format_consistency():
    """Test if the format of assignments is consistent."""
    print("\n=== Testing assignment format consistency ===")
    
    # For rectangular matrices, check if assignments always follow the expected format
    cost_matrix = jnp.array([[1, 2, 3],
                              [4, 5, 6]], dtype=jnp.float32)
    
    print(f"Cost matrix shape: {cost_matrix.shape} (2 rows, 3 cols)")
    print(f"Expected: min(2,3) = 2 assignments")
    
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
    
    print(f"\nhungarian_algorithm:")
    print(f"  Row indices: {i1.tolist()} (sorted: {sorted(i1.tolist())})")
    print(f"  Col indices: {j1.tolist()} (sorted: {sorted(j1.tolist())})")
    print(f"  Are row indices sequential 0,1? {i1.tolist() == [0, 1] or sorted(i1.tolist()) == [0, 1]}")
    
    print(f"\nbase_hungarian_algorithm:")
    print(f"  Row indices: {i2.tolist()} (sorted: {sorted(i2.tolist())})")
    print(f"  Col indices: {j2.tolist()} (sorted: {sorted(j2.tolist())})")
    print(f"  Are row indices sequential 0,1? {i2.tolist() == [0, 1] or sorted(i2.tolist()) == [0, 1]}")
    
    # Check the opposite case (more rows than columns)
    cost_matrix_T = cost_matrix.T
    print(f"\n--- Transposed case ---")
    print(f"Cost matrix shape: {cost_matrix_T.shape} (3 rows, 2 cols)")
    print(f"Expected: min(3,2) = 2 assignments")
    
    i1_T, j1_T = assignment.hungarian_algorithm(cost_matrix_T)
    i2_T, j2_T = assignment.base_hungarian_algorithm(cost_matrix_T)
    
    print(f"\nhungarian_algorithm:")
    print(f"  Row indices: {i1_T.tolist()} (sorted: {sorted(i1_T.tolist())})")
    print(f"  Col indices: {j1_T.tolist()} (sorted: {sorted(j1_T.tolist())})")
    
    print(f"\nbase_hungarian_algorithm:")
    print(f"  Row indices: {i2_T.tolist()} (sorted: {sorted(i2_T.tolist())})")
    print(f"  Col indices: {j2_T.tolist()} (sorted: {sorted(j2_T.tolist())})")


if __name__ == "__main__":
    test_rectangular_matrices_costs()
    test_specific_rectangular_case()
    test_edge_case_single_element()
    test_assignment_format_consistency()