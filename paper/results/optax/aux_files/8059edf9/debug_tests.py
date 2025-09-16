#!/usr/bin/env python3
"""Debug tests to investigate potential bugs in Hungarian algorithm."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax
import jax.numpy as jnp
from optax import assignment

# Disable JIT to avoid timing issues
jax.config.update('jax_disable_jit', True)

def test_simple_case():
    """Test a simple 2x1 matrix."""
    print("\n=== Testing simple 2x1 matrix ===")
    
    # This is the failing example from Hypothesis
    cost_matrix = jnp.array([[-0., 0.]], dtype=jnp.float32)
    print(f"Cost matrix shape: {cost_matrix.shape}")
    print(f"Cost matrix:\n{cost_matrix}")
    
    try:
        i1, j1 = assignment.hungarian_algorithm(cost_matrix)
        print(f"hungarian_algorithm result: i={i1}, j={j1}")
        if len(i1) > 0:
            print(f"Cost: {cost_matrix[i1, j1].sum()}")
    except Exception as e:
        print(f"hungarian_algorithm failed: {e}")
    
    try:
        i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
        print(f"base_hungarian_algorithm result: i={i2}, j={j2}")
        if len(i2) > 0:
            print(f"Cost: {cost_matrix[i2, j2].sum()}")
    except Exception as e:
        print(f"base_hungarian_algorithm failed: {e}")


def test_all_zeros_matrix():
    """Test matrices with all zeros."""
    print("\n=== Testing all-zeros matrices ===")
    
    for shape in [(1, 1), (2, 2), (3, 3), (3, 2), (2, 3)]:
        cost_matrix = jnp.zeros(shape, dtype=jnp.float32)
        print(f"\nShape: {shape}")
        
        try:
            i1, j1 = assignment.hungarian_algorithm(cost_matrix)
            cost1 = cost_matrix[i1, j1].sum() if len(i1) > 0 else 0
            print(f"  hungarian: indices=({i1.tolist()}, {j1.tolist()}), cost={cost1}")
        except Exception as e:
            print(f"  hungarian failed: {e}")
        
        try:
            i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
            cost2 = cost_matrix[i2, j2].sum() if len(i2) > 0 else 0
            print(f"  base: indices=({i2.tolist()}, {j2.tolist()}), cost={cost2}")
        except Exception as e:
            print(f"  base failed: {e}")


def test_single_column_matrices():
    """Test matrices with single column."""
    print("\n=== Testing single-column matrices ===")
    
    for n_rows in [1, 2, 5, 10]:
        cost_matrix = jnp.zeros((n_rows, 1), dtype=jnp.float32)
        print(f"\nShape: {cost_matrix.shape}")
        
        try:
            i1, j1 = assignment.hungarian_algorithm(cost_matrix)
            print(f"  hungarian: i={i1.tolist()}, j={j1.tolist()}")
            # Check for duplicates
            if len(i1) != len(set(i1.tolist())):
                print(f"  WARNING: Duplicate row indices in hungarian!")
            if len(j1) != len(set(j1.tolist())):
                print(f"  WARNING: Duplicate column indices in hungarian!")
        except Exception as e:
            print(f"  hungarian failed: {e}")
        
        try:
            i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)  
            print(f"  base: i={i2.tolist()}, j={j2.tolist()}")
            # Check for duplicates
            if len(i2) != len(set(i2.tolist())):
                print(f"  WARNING: Duplicate row indices in base!")
            if len(j2) != len(set(j2.tolist())):
                print(f"  WARNING: Duplicate column indices in base!")
        except Exception as e:
            print(f"  base failed: {e}")


def test_negative_zeros():
    """Test matrix with -0.0 values."""
    print("\n=== Testing negative zero ===")
    
    # Create matrix with negative zero
    cost_matrix = jnp.array([[-0.0, 0.0, 1.0],
                              [0.0, -0.0, 2.0],
                              [3.0, 4.0, -0.0]], dtype=jnp.float32)
    
    print(f"Cost matrix:\n{cost_matrix}")
    
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
    
    cost1 = cost_matrix[i1, j1].sum()
    cost2 = cost_matrix[i2, j2].sum()
    
    print(f"hungarian: i={i1.tolist()}, j={j1.tolist()}, cost={cost1}")
    print(f"base: i={i2.tolist()}, j={j2.tolist()}, cost={cost2}")
    
    if not jnp.allclose(cost1, cost2):
        print(f"ERROR: Costs differ! {cost1} vs {cost2}")


def test_transpose_consistency():
    """Test if transpose handling is consistent."""
    print("\n=== Testing transpose consistency ===")
    
    # Test a rectangular matrix and its transpose
    cost_matrix = jnp.array([[1.0, 2.0],
                              [3.0, 4.0],
                              [5.0, 6.0]], dtype=jnp.float32)
    
    print(f"Original shape: {cost_matrix.shape}")
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
    print(f"  hungarian: i={i1.tolist()}, j={j1.tolist()}")
    print(f"  base: i={i2.tolist()}, j={j2.tolist()}")
    
    cost_matrix_T = cost_matrix.T
    print(f"\nTransposed shape: {cost_matrix_T.shape}")
    i1_T, j1_T = assignment.hungarian_algorithm(cost_matrix_T)
    i2_T, j2_T = assignment.base_hungarian_algorithm(cost_matrix_T)
    print(f"  hungarian: i={i1_T.tolist()}, j={j1_T.tolist()}")
    print(f"  base: i={i2_T.tolist()}, j={j2_T.tolist()}")


if __name__ == "__main__":
    test_simple_case()
    test_all_zeros_matrix()
    test_single_column_matrices()
    test_negative_zeros()
    test_transpose_consistency()