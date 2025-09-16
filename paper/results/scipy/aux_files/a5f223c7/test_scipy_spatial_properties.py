import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings
import scipy.spatial
import scipy.spatial.distance as dist
import math


# Strategy for valid float arrays
def valid_arrays(min_size=1, max_size=100, min_value=-1e6, max_value=1e6):
    return st.lists(
        st.floats(
            min_value=min_value,
            max_value=max_value,
            allow_nan=False,
            allow_infinity=False
        ),
        min_size=min_size,
        max_size=max_size
    ).map(np.array)


# Strategy for arrays of same size
@st.composite
def same_size_arrays(draw, min_size=1, max_size=100):
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    arr1 = draw(st.lists(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=size, max_size=size
    ))
    arr2 = draw(st.lists(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=size, max_size=size
    ))
    return np.array(arr1), np.array(arr2)


# Test 1: Distance function symmetry
@given(same_size_arrays())
def test_distance_symmetry(arrays):
    u, v = arrays
    d1 = dist.euclidean(u, v)
    d2 = dist.euclidean(v, u)
    assert math.isclose(d1, d2, rel_tol=1e-9), f"Distance not symmetric: {d1} != {d2}"


# Test 2: Distance non-negativity
@given(same_size_arrays())
def test_distance_non_negative(arrays):
    u, v = arrays
    d = dist.euclidean(u, v)
    assert d >= 0, f"Distance is negative: {d}"


# Test 3: Distance to itself is zero
@given(valid_arrays(min_size=1, max_size=100))
def test_distance_identity(arr):
    d = dist.euclidean(arr, arr)
    assert math.isclose(d, 0, abs_tol=1e-10), f"Distance to itself is not zero: {d}"


# Test 4: Euclidean is Minkowski with p=2
@given(same_size_arrays())
def test_euclidean_minkowski_equivalence(arrays):
    u, v = arrays
    euclidean_dist = dist.euclidean(u, v)
    minkowski_dist = dist.minkowski(u, v, p=2)
    assert math.isclose(euclidean_dist, minkowski_dist, rel_tol=1e-9), \
        f"Euclidean {euclidean_dist} != Minkowski(p=2) {minkowski_dist}"


# Test 5: Triangle inequality for euclidean distance
@st.composite
def three_same_size_arrays(draw):
    size = draw(st.integers(min_value=1, max_value=50))
    arrays = []
    for _ in range(3):
        arr = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=size, max_size=size
        ))
        arrays.append(np.array(arr))
    return arrays


@given(three_same_size_arrays())
def test_triangle_inequality(arrays):
    a, b, c = arrays
    ab = dist.euclidean(a, b)
    bc = dist.euclidean(b, c)
    ac = dist.euclidean(a, c)
    # Triangle inequality: d(a,c) <= d(a,b) + d(b,c)
    assert ac <= ab + bc + 1e-10, f"Triangle inequality violated: {ac} > {ab} + {bc}"


# Test 6: ConvexHull - all points should be inside or on the hull
@st.composite
def points_2d(draw, min_points=4, max_points=20):
    n_points = draw(st.integers(min_value=min_points, max_value=max_points))
    points = []
    for _ in range(n_points):
        x = draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
        y = draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
        points.append([x, y])
    return np.array(points)


@given(points_2d())
def test_convex_hull_contains_points(points):
    try:
        hull = scipy.spatial.ConvexHull(points)
        # All input points should have non-positive distance to hull
        # (negative means inside, 0 means on boundary)
        for point in points:
            # Check if point is inside hull using hull equations
            # Ax + b <= 0 for all equations means inside
            distances = hull.equations @ np.append(point, 1)
            assert np.all(distances <= 1e-6), f"Point {point} is outside hull"
    except scipy.spatial.QhullError:
        # Skip degenerate cases
        assume(False)


# Test 7: ConvexHull volume is non-negative
@given(points_2d(min_points=4, max_points=15))
def test_convex_hull_volume_non_negative(points):
    try:
        hull = scipy.spatial.ConvexHull(points)
        assert hull.volume >= -1e-10, f"Hull volume is negative: {hull.volume}"
    except scipy.spatial.QhullError:
        assume(False)


# Test 8: KDTree - nearest neighbor to a point in tree is itself
@st.composite
def kdtree_data(draw):
    n_points = draw(st.integers(min_value=1, max_value=50))
    n_dims = draw(st.integers(min_value=1, max_value=5))
    points = []
    for _ in range(n_points):
        point = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=n_dims, max_size=n_dims
        ))
        points.append(point)
    return np.array(points)


@given(kdtree_data())
def test_kdtree_self_nearest_neighbor(points):
    tree = scipy.spatial.KDTree(points)
    for i, point in enumerate(points):
        distance, index = tree.query(point, k=1)
        assert index == i, f"Nearest neighbor to point {i} is {index}, not itself"
        assert math.isclose(distance, 0, abs_tol=1e-10), f"Distance to itself is {distance}, not 0"


# Test 9: KDTree query with k=n returns all points
@given(kdtree_data())
def test_kdtree_query_all(points):
    n = len(points)
    assume(n > 1)  # Need at least 2 points for meaningful test
    tree = scipy.spatial.KDTree(points)
    # Query from first point
    distances, indices = tree.query(points[0], k=min(n, 100))  # Cap at 100 for performance
    # All indices should be unique and in range
    assert len(set(indices)) == len(indices), "Duplicate indices in KDTree query"
    assert all(0 <= idx < n for idx in indices), "Invalid index returned by KDTree"


# Test 10: geometric_slerp boundary conditions
@st.composite  
def unit_vectors(draw):
    # Generate two different unit vectors
    dim = draw(st.integers(min_value=2, max_value=5))
    
    # First vector
    v1 = draw(st.lists(
        st.floats(min_value=-1, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=dim, max_size=dim
    ))
    v1 = np.array(v1)
    norm1 = np.linalg.norm(v1)
    assume(norm1 > 1e-6)  # Avoid zero vector
    v1 = v1 / norm1
    
    # Second vector (different from first)
    v2 = draw(st.lists(
        st.floats(min_value=-1, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=dim, max_size=dim
    ))
    v2 = np.array(v2)
    norm2 = np.linalg.norm(v2)
    assume(norm2 > 1e-6)
    v2 = v2 / norm2
    
    # Ensure they're not too close (avoid numerical issues)
    assume(np.abs(np.dot(v1, v2)) < 0.999)
    
    return v1, v2


@given(unit_vectors())
def test_geometric_slerp_boundaries(vectors):
    start, end = vectors
    
    # At t=0, should return start
    result_0 = scipy.spatial.geometric_slerp(start, end, 0)
    assert np.allclose(result_0, start, rtol=1e-9), f"slerp(t=0) != start"
    
    # At t=1, should return end
    result_1 = scipy.spatial.geometric_slerp(start, end, 1)
    assert np.allclose(result_1, end, rtol=1e-9), f"slerp(t=1) != end"
    
    # Result should be on unit sphere for any t in [0,1]
    t_values = np.linspace(0, 1, 5)
    results = scipy.spatial.geometric_slerp(start, end, t_values)
    for i, result in enumerate(results):
        norm = np.linalg.norm(result)
        assert math.isclose(norm, 1.0, rel_tol=1e-9), \
            f"slerp result at t={t_values[i]} not on unit sphere: norm={norm}"


# Test 11: cdist symmetry when computing distances between same set
@st.composite
def point_set(draw):
    n_points = draw(st.integers(min_value=2, max_value=10))
    n_dims = draw(st.integers(min_value=1, max_value=5))
    points = []
    for _ in range(n_points):
        point = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=n_dims, max_size=n_dims
        ))
        points.append(point)
    return np.array(points)


@given(point_set())
def test_cdist_self_symmetry(points):
    # Distance matrix of points to themselves should be symmetric
    D = dist.cdist(points, points)
    assert np.allclose(D, D.T, rtol=1e-9), "cdist self-distance matrix not symmetric"
    # Diagonal should be zeros
    assert np.allclose(np.diag(D), 0, atol=1e-10), "cdist diagonal not zero"


# Test 12: distance_matrix properties
@st.composite
def two_point_sets(draw):
    n_dims = draw(st.integers(min_value=1, max_value=5))
    n_points1 = draw(st.integers(min_value=1, max_value=10))
    n_points2 = draw(st.integers(min_value=1, max_value=10))
    
    points1 = []
    for _ in range(n_points1):
        point = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=n_dims, max_size=n_dims
        ))
        points1.append(point)
        
    points2 = []
    for _ in range(n_points2):
        point = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=n_dims, max_size=n_dims
        ))
        points2.append(point)
        
    return np.array(points1), np.array(points2)


@given(two_point_sets())
def test_distance_matrix_properties(point_sets):
    x, y = point_sets
    D = scipy.spatial.distance_matrix(x, y)
    
    # All distances should be non-negative
    assert np.all(D >= -1e-10), "Negative distance in distance_matrix"
    
    # Shape should be correct
    assert D.shape == (len(x), len(y)), f"Wrong shape: {D.shape} != ({len(x)}, {len(y)})"
    
    # Test specific distances match
    for i in range(min(3, len(x))):
        for j in range(min(3, len(y))):
            expected = np.linalg.norm(x[i] - y[j])
            assert math.isclose(D[i, j], expected, rel_tol=1e-9), \
                f"Distance mismatch at ({i},{j}): {D[i,j]} != {expected}"