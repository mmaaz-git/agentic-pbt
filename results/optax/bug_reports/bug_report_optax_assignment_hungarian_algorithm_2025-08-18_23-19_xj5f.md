# Bug Report: optax.assignment.hungarian_algorithm Documentation Example Mismatch

**Target**: `optax.assignment.hungarian_algorithm`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The documentation example in `hungarian_algorithm` shows incorrect expected output for the row and column indices, though the total cost is correct.

## Property-Based Test

```python
@given(st.just(jnp.array([[8, 4, 7], [5, 2, 3], [9, 6, 7], [9, 4, 8]])))
def test_documentation_example_accuracy(cost_matrix):
    """Test that the documentation example output matches actual output."""
    i, j = assignment.hungarian_algorithm(cost_matrix)
    
    # Documentation claims i=[0, 1, 3] and j=[0, 2, 1]
    assert i.tolist() == [0, 1, 3], f"Expected i=[0, 1, 3], got {i.tolist()}"
    assert j.tolist() == [0, 2, 1], f"Expected j=[0, 2, 1], got {j.tolist()}"
```

**Failing input**: The example matrix from the documentation itself

## Reproducing the Bug

```python
import jax.numpy as jnp
from optax import assignment

cost = jnp.array([
    [8, 4, 7],
    [5, 2, 3],
    [9, 6, 7],
    [9, 4, 8],
])

i, j = assignment.hungarian_algorithm(cost)

print(f"Actual: i={i.tolist()}, j={j.tolist()}")
print(f"Docstring claims: i=[0, 1, 3], j=[0, 2, 1]")
print(f"Match: {i.tolist() == [0, 1, 3] and j.tolist() == [0, 2, 1]}")
```

## Why This Is A Bug

The function's docstring (lines 422-424) shows specific expected output that doesn't match the actual function behavior. While both achieve the same optimal cost (15), the returned indices are in a different order. This violates the API contract as specified in the documentation. The `base_hungarian_algorithm` returns the indices shown in the documentation, suggesting the example may have been copied from that function.

## Fix

```diff
--- a/optax/assignment/_hungarian_algorithm.py
+++ b/optax/assignment/_hungarian_algorithm.py
@@ -419,10 +419,10 @@ def hungarian_algorithm(cost_matrix):
     ...    [9, 4, 8],
     ...  ])
     >>> i, j = optax.assignment.hungarian_algorithm(cost)
     >>> print("cost:", cost[i, j].sum())
     cost: 15
-    >>> print("i:", i)
-    i: [0 1 3]
-    >>> print("j:", j)
-    j: [0 2 1]
+    # Note: The specific indices may vary between optimal solutions
+    # The algorithm guarantees optimal cost but not a specific assignment order
     >>> cost = jnp.array(
     ...  [
     ...    [90, 80, 75, 70],
```