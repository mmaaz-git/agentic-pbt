"""
Demonstrates unexpected KDTree behavior with duplicate points.
When querying for nearest neighbor of a point that exists in the tree,
it doesn't always return that point's index when duplicates exist.
"""

import numpy as np
import scipy.spatial


def test_kdtree_duplicate_points():
    # Simple case: two identical points
    points = np.array([[0.0], [0.0]])
    tree = scipy.spatial.KDTree(points)
    
    print("Test 1: Two identical points at [0.0]")
    print("Points:", points.flatten())
    
    for i in range(len(points)):
        dist, idx = tree.query(points[i], k=1)
        print(f"  Query point {i}: nearest neighbor index = {idx}, distance = {dist}")
        if idx != i and dist == 0:
            print(f"    ⚠️  Expected index {i} but got {idx} (both points are identical)")
    
    print("\nTest 2: Multiple groups of duplicate points")
    # Points: [A, B, A, C, B, A] where A, B, C are different coordinates
    points = np.array([[1.0, 0.0],   # index 0: A
                       [2.0, 0.0],   # index 1: B  
                       [1.0, 0.0],   # index 2: A (duplicate of 0)
                       [3.0, 0.0],   # index 3: C
                       [2.0, 0.0],   # index 4: B (duplicate of 1)
                       [1.0, 0.0]])  # index 5: A (duplicate of 0 and 2)
    
    tree = scipy.spatial.KDTree(points)
    
    print("Points:")
    for i, p in enumerate(points):
        print(f"  {i}: {p}")
    
    print("\nQuerying each point for its nearest neighbor:")
    issues = []
    for i in range(len(points)):
        dist, idx = tree.query(points[i], k=1)
        status = "✓" if idx == i else "✗"
        print(f"  Point {i}: nearest = {idx}, distance = {dist:.1f} {status}")
        if idx != i and dist == 0:
            issues.append((i, idx))
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} cases where duplicate points don't return themselves:")
        for point_idx, returned_idx in issues:
            print(f"  - Point {point_idx} returned {returned_idx} (both at {points[point_idx]})")
    
    # Test with cKDTree for comparison
    print("\n" + "="*50)
    print("Testing with cKDTree (C implementation):")
    ctree = scipy.spatial.cKDTree(points)
    
    c_issues = []
    for i in range(len(points)):
        dist, idx = ctree.query(points[i], k=1)
        if idx != i and dist == 0:
            c_issues.append((i, idx))
    
    print(f"cKDTree: {len(c_issues)} cases where duplicate points don't return themselves")
    
    return len(issues) > 0 or len(c_issues) > 0


if __name__ == "__main__":
    has_issue = test_kdtree_duplicate_points()
    
    if has_issue:
        print("\n" + "="*50)
        print("SUMMARY: KDTree.query() has unexpected behavior with duplicate points.")
        print("When a point exists multiple times in the tree, querying for that")
        print("point's nearest neighbor may return a different instance of the")
        print("same coordinate, rather than the queried point's own index.")
        print("\nThis behavior is:")
        print("1. Unintuitive (nearest neighbor to a point should be itself)")
        print("2. Undocumented in the KDTree.query() docstring")
        print("3. Inconsistent with user expectations")
        print("4. Could cause issues in algorithms relying on self-queries")