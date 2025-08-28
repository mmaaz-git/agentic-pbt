"""Property-based tests for the Hungarian algorithm in optax.assignment."""

import math
from hypothesis import given, strategies as st, settings, assume
import jax
import jax.numpy as jnp
import numpy as np
from optax import assignment


# Strategy for reasonable matrix dimensions
matrix_dims = st.tuples(
    st.integers(min_value=0, max_value=50),  # rows
    st.integers(min_value=0, max_value=50)   # columns
)

# Strategy for cost matrices with regular float values
@st.composite
def cost_matrices(draw, min_size=0, max_size=50):
    rows = draw(st.integers(min_value=min_size, max_value=max_size))
    cols = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Generate cost matrix with reasonable values
    elements = st.floats(
        min_value=-1e6, 
        max_value=1e6, 
        allow_nan=False, 
        allow_infinity=False
    )
    
    # Create matrix as numpy array first, then convert to JAX
    matrix_list = draw(st.lists(
        st.lists(elements, min_size=cols, max_size=cols),
        min_size=rows, max_size=rows
    ))
    
    if rows == 0 or cols == 0:
        return jnp.zeros((rows, cols))
    
    return jnp.array(matrix_list)


# Strategy for cost matrices that may contain inf values
@st.composite
def cost_matrices_with_inf(draw, min_size=1, max_size=20):
    rows = draw(st.integers(min_value=min_size, max_value=max_size))
    cols = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Mix of regular values and inf
    elements = st.one_of(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        st.just(float('inf'))
    )
    
    matrix_list = draw(st.lists(
        st.lists(elements, min_size=cols, max_size=cols),
        min_size=rows, max_size=rows
    ))
    
    # Ensure at least one path exists without inf
    # by having at least one complete row/column without inf
    matrix = np.array(matrix_list, dtype=float)
    
    # Check if there's a feasible solution
    # (at least one finite value in each row and column for min(rows, cols) assignments)
    # For simplicity, we'll sometimes just skip infeasible matrices
    if np.all(np.isinf(matrix)):
        # All inf is definitely infeasible
        assume(False)
    
    return jnp.array(matrix)


@given(cost_matrices())
@settings(max_examples=100)
def test_two_implementations_same_cost(cost_matrix):
    """Both Hungarian algorithm implementations should produce same total cost."""
    if cost_matrix.shape[0] == 0 or cost_matrix.shape[1] == 0:
        # Skip empty matrices as they're trivial
        return
    
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.base_hungarian_algorithm(cost_matrix)
    
    cost1 = cost_matrix[i1, j1].sum()
    cost2 = cost_matrix[i2, j2].sum()
    
    # The costs should be very close (allowing for floating point differences)
    assert jnp.allclose(cost1, cost2, rtol=1e-5, atol=1e-8), \
        f"Different costs: {cost1} vs {cost2}"


@given(cost_matrices())
@settings(max_examples=100)
def test_assignment_count_invariant(cost_matrix):
    """Number of assignments should equal min(n, m)."""
    n, m = cost_matrix.shape
    expected_assignments = min(n, m)
    
    i, j = assignment.hungarian_algorithm(cost_matrix)
    
    assert len(i) == expected_assignments, \
        f"Expected {expected_assignments} assignments, got {len(i)}"
    assert len(j) == expected_assignments, \
        f"Expected {expected_assignments} assignments, got {len(j)}"


@given(cost_matrices())
@settings(max_examples=100)
def test_unique_assignments(cost_matrix):
    """Each row and column should be assigned at most once."""
    if cost_matrix.shape[0] == 0 or cost_matrix.shape[1] == 0:
        return
    
    i, j = assignment.hungarian_algorithm(cost_matrix)
    
    # Check uniqueness of row assignments
    assert len(i) == len(set(i.tolist())), \
        f"Duplicate row assignments: {i}"
    
    # Check uniqueness of column assignments
    assert len(j) == len(set(j.tolist())), \
        f"Duplicate column assignments: {j}"
    
    # Check that all indices are in valid range
    assert jnp.all(i >= 0) and jnp.all(i < cost_matrix.shape[0]), \
        f"Row indices out of range: {i}"
    assert jnp.all(j >= 0) and jnp.all(j < cost_matrix.shape[1]), \
        f"Column indices out of range: {j}"


@given(cost_matrices(min_size=1, max_size=30))
@settings(max_examples=50)
def test_transpose_property(cost_matrix):
    """Transposing cost matrix should yield transposed assignment with same cost."""
    n, m = cost_matrix.shape
    
    # Get assignment for original matrix
    i1, j1 = assignment.hungarian_algorithm(cost_matrix)
    cost1 = cost_matrix[i1, j1].sum()
    
    # Get assignment for transposed matrix
    cost_matrix_T = cost_matrix.T
    i2, j2 = assignment.hungarian_algorithm(cost_matrix_T)
    cost2 = cost_matrix_T[i2, j2].sum()
    
    # Costs should be the same
    assert jnp.allclose(cost1, cost2, rtol=1e-5, atol=1e-8), \
        f"Different costs for transpose: {cost1} vs {cost2}"
    
    # The assignments should correspond
    # i2, j2 for transposed should relate to j1, i1 for original
    # But the exact correspondence depends on the implementation details
    # So we just verify the cost invariant


@given(cost_matrices())
@settings(max_examples=100)
def test_deterministic_cost(cost_matrix):
    """Same input should always produce same total cost."""
    if cost_matrix.shape[0] == 0 or cost_matrix.shape[1] == 0:
        return
    
    # Run multiple times
    costs = []
    for _ in range(3):
        i, j = assignment.hungarian_algorithm(cost_matrix)
        costs.append(cost_matrix[i, j].sum())
    
    # All costs should be identical
    for cost in costs[1:]:
        assert jnp.allclose(costs[0], cost, rtol=1e-10, atol=1e-10), \
            f"Non-deterministic costs: {costs}"


@given(cost_matrices_with_inf())
@settings(max_examples=50)
def test_inf_handling(cost_matrix):
    """Algorithm should handle matrices with inf values."""
    # Just test that it doesn't crash and produces valid output format
    try:
        i, j = assignment.hungarian_algorithm(cost_matrix)
        
        # Basic sanity checks
        expected_assignments = min(cost_matrix.shape)
        assert len(i) == expected_assignments
        assert len(j) == expected_assignments
        
        # If there are assignments, they should be valid indices
        if len(i) > 0:
            assert jnp.all(i >= 0) and jnp.all(i < cost_matrix.shape[0])
            assert jnp.all(j >= 0) and jnp.all(j < cost_matrix.shape[1])
            
            # The total cost might be inf if all paths include inf
            total_cost = cost_matrix[i, j].sum()
            # This is valid - could be finite or inf
            
    except Exception as e:
        # Log the error for investigation
        print(f"Error with inf matrix of shape {cost_matrix.shape}: {e}")
        raise


@given(st.integers(min_value=1, max_value=20))
@settings(max_examples=50)
def test_zero_cost_optimal(n):
    """When zero-cost perfect matching exists, algorithm should find it."""
    # Create a cost matrix where diagonal is 0 and everything else is positive
    cost_matrix = jnp.ones((n, n)) * 10
    cost_matrix = cost_matrix.at[jnp.arange(n), jnp.arange(n)].set(0)
    
    i, j = assignment.hungarian_algorithm(cost_matrix)
    total_cost = cost_matrix[i, j].sum()
    
    # The optimal cost should be 0 (taking all diagonal elements)
    assert jnp.allclose(total_cost, 0, atol=1e-10), \
        f"Failed to find zero-cost solution: cost={total_cost}"


@given(cost_matrices(min_size=1, max_size=20))
@settings(max_examples=50)
def test_base_vs_optimized_consistency(cost_matrix):
    """base_hungarian_algorithm and hungarian_algorithm should agree on cost."""
    i1, j1 = assignment.base_hungarian_algorithm(cost_matrix)
    i2, j2 = assignment.hungarian_algorithm(cost_matrix)
    
    cost1 = cost_matrix[i1, j1].sum()
    cost2 = cost_matrix[i2, j2].sum()
    
    # Both should find the same optimal cost
    assert jnp.allclose(cost1, cost2, rtol=1e-5, atol=1e-8), \
        f"Implementations disagree: base={cost1}, optimized={cost2}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])