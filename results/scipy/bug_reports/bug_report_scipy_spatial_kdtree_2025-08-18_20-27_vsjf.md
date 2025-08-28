# Bug Report: scipy.spatial.KDTree Duplicate Point Index Inconsistency

**Target**: `scipy.spatial.KDTree.query` and `scipy.spatial.cKDTree.query`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

KDTree.query() returns inconsistent indices when querying duplicate points - it may return a different instance of the same coordinate rather than the queried point's own index, violating the expected behavior that a point's nearest neighbor is itself.

## Property-Based Test

```python
@given(kdtree_data())
def test_kdtree_self_nearest_neighbor(points):
    tree = scipy.spatial.KDTree(points)
    for i, point in enumerate(points):
        distance, index = tree.query(point, k=1)
        assert index == i, f"Nearest neighbor to point {i} is {index}, not itself"
        assert math.isclose(distance, 0, abs_tol=1e-10), f"Distance to itself is {distance}, not 0"
```

**Failing input**: `array([[0.], [0.]])`

## Reproducing the Bug

```python
import numpy as np
import scipy.spatial

points = np.array([[0.0], [0.0]])
tree = scipy.spatial.KDTree(points)

for i in range(len(points)):
    dist, idx = tree.query(points[i], k=1)
    print(f"Point {i}: nearest neighbor index = {idx}, distance = {dist}")

# Output:
# Point 0: nearest neighbor index = 0, distance = 0.0
# Point 1: nearest neighbor index = 0, distance = 0.0
# Point 1 should return index 1 (itself), not 0
```

## Why This Is A Bug

This violates the intuitive and mathematical expectation that the nearest neighbor to a point that exists in the tree should be itself. While the distance is correctly reported as 0, the index returned is not the queried point's own index when duplicates exist. This behavior is:

1. **Undocumented** - The KDTree.query() docstring doesn't mention this edge case
2. **Unintuitive** - Users expect self-queries to return the point itself
3. **Potentially breaking** - Algorithms that rely on index consistency (e.g., using KDTree to find corresponding points in tracking applications) will fail
4. **Inconsistent** - The first occurrence of duplicates returns itself, but later occurrences don't

## Fix

The issue likely stems from how the tree handles ties when multiple points have the same distance. A high-level fix would involve modifying the query algorithm to prefer returning the queried point's own index when distances are equal (tie-breaking on index equality). The implementation would need changes in both the Python KDTree and C-based cKDTree to ensure consistent behavior.