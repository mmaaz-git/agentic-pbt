import numpy as np
from hypothesis import given, strategies as st, assume, settings
import scipy.cluster.vq as vq
import scipy.cluster.hierarchy as hier
import math
import pytest


# Strategy for generating valid observation matrices
@st.composite
def observations(draw, min_samples=2, max_samples=100, min_features=1, max_features=10):
    n_samples = draw(st.integers(min_value=min_samples, max_value=max_samples))
    n_features = draw(st.integers(min_value=min_features, max_value=max_features))
    # Generate non-degenerate data with reasonable values
    data = draw(st.lists(
        st.lists(
            st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
            min_size=n_features, max_size=n_features
        ),
        min_size=n_samples, max_size=n_samples
    ))
    return np.array(data)


# Test 1: whiten should produce unit variance
@given(observations(min_samples=3, max_samples=50, min_features=2, max_features=8))
def test_whiten_unit_variance(obs):
    # Skip if any feature has zero variance (would cause division by zero)
    stds = np.std(obs, axis=0)
    assume(np.all(stds > 1e-10))
    
    whitened = vq.whiten(obs)
    
    # Each feature should have unit variance after whitening
    whitened_stds = np.std(whitened, axis=0)
    for i, std in enumerate(whitened_stds):
        assert math.isclose(std, 1.0, rel_tol=1e-9), f"Feature {i} std is {std}, expected 1.0"


# Test 2: vq assignment validity
@given(
    observations(min_samples=5, max_samples=30, min_features=2, max_features=5),
    st.integers(min_value=2, max_value=10)
)
def test_vq_assignment_validity(obs, n_codes):
    # Generate a simple codebook from first n_codes observations
    assume(len(obs) >= n_codes)
    codebook = obs[:n_codes].copy()
    
    codes, distortion = vq.vq(obs, codebook)
    
    # All codes should be valid indices
    assert np.all(codes >= 0), "Some codes are negative"
    assert np.all(codes < n_codes), f"Some codes >= {n_codes}"
    assert len(codes) == len(obs), "Number of codes doesn't match observations"
    
    # Each observation should be assigned to its nearest codebook entry
    for i, observation in enumerate(obs):
        distances = np.sqrt(np.sum((codebook - observation)**2, axis=1))
        expected_code = np.argmin(distances)
        assert codes[i] == expected_code, f"Obs {i} assigned to {codes[i]}, expected {expected_code}"


# Test 3: kmeans basic properties
@given(
    observations(min_samples=10, max_samples=50, min_features=2, max_features=5),
    st.integers(min_value=2, max_value=8)
)
@settings(max_examples=100)
def test_kmeans_properties(obs, k):
    assume(len(obs) >= k)
    # Ensure non-degenerate data
    assume(np.std(obs) > 1e-10)
    
    # Run kmeans
    centroids, distortion = vq.kmeans(obs, k, seed=42)
    
    # Should return k centroids
    assert len(centroids) == k, f"Expected {k} centroids, got {len(centroids)}"
    assert centroids.shape[1] == obs.shape[1], "Centroid dimensions don't match observations"
    
    # Distortion should be non-negative
    assert distortion >= 0, f"Distortion is negative: {distortion}"
    
    # All centroids should be finite
    assert np.all(np.isfinite(centroids)), "Some centroids are not finite"


# Test 4: kmeans2 returns valid clusters
@given(
    observations(min_samples=10, max_samples=40, min_features=2, max_features=5),
    st.integers(min_value=2, max_value=6)
)
@settings(max_examples=100)
def test_kmeans2_validity(obs, k):
    assume(len(obs) >= k)
    assume(np.std(obs) > 1e-10)
    
    centroids, labels = vq.kmeans2(obs, k, minit='points', seed=42)
    
    # Check shapes
    assert len(centroids) == k, f"Expected {k} centroids, got {len(centroids)}"
    assert len(labels) == len(obs), "Label count doesn't match observation count"
    
    # All labels should be valid cluster indices
    assert np.all(labels >= 0), "Some labels are negative"
    assert np.all(labels < k), f"Some labels >= {k}"
    
    # All clusters should have at least one point (for minit='points')
    unique_labels = np.unique(labels)
    assert len(unique_labels) <= k, f"More unique labels than clusters"


# Test 5: linkage matrix validity round-trip
@given(observations(min_samples=3, max_samples=20, min_features=2, max_features=5))
def test_linkage_validity_roundtrip(obs):
    # Create linkage matrix
    Z = hier.linkage(obs, method='single')
    
    # Should be valid
    assert hier.is_valid_linkage(Z), "Generated linkage matrix is not valid"
    
    # Check dimensions
    n = len(obs)
    assert Z.shape == (n-1, 4), f"Expected shape {(n-1, 4)}, got {Z.shape}"
    
    # Distances should be non-negative
    assert np.all(Z[:, 2] >= 0), "Some distances are negative"


# Test 6: linkage monotonicity for single/complete methods
@given(observations(min_samples=3, max_samples=15, min_features=2, max_features=4))
def test_linkage_monotonicity(obs):
    # Single and complete linkage should produce monotonic results
    for method in ['single', 'complete']:
        Z = hier.linkage(obs, method=method)
        assert hier.is_monotonic(Z), f"{method} linkage is not monotonic"


# Test 7: cophenet correlation coefficient bounds
@given(observations(min_samples=4, max_samples=15, min_features=2, max_features=4))
def test_cophenet_bounds(obs):
    # Create linkage and compute cophenetic correlation
    from scipy.spatial.distance import pdist
    
    Z = hier.linkage(obs, method='average')
    Y = pdist(obs)
    
    c, coph_dists = hier.cophenet(Z, Y)
    
    # Correlation coefficient should be between -1 and 1
    assert -1.0 <= c <= 1.0, f"Cophenetic correlation {c} outside [-1, 1]"
    
    # Cophenetic distances should be non-negative
    assert np.all(coph_dists >= 0), "Some cophenetic distances are negative"


# Test 8: fcluster produces valid cluster assignments
@given(
    observations(min_samples=4, max_samples=15, min_features=2, max_features=3),
    st.integers(min_value=1, max_value=5)
)
def test_fcluster_validity(obs, n_clusters):
    assume(n_clusters < len(obs))
    
    Z = hier.linkage(obs, method='ward')
    clusters = hier.fcluster(Z, n_clusters, criterion='maxclust')
    
    # Should assign a cluster to each observation
    assert len(clusters) == len(obs), "Cluster count doesn't match observation count"
    
    # Clusters should be numbered from 1 to at most n_clusters
    unique_clusters = np.unique(clusters)
    assert np.all(unique_clusters >= 1), "Some clusters < 1"
    assert np.all(unique_clusters <= n_clusters), f"Some clusters > {n_clusters}"
    assert len(unique_clusters) <= n_clusters, "More unique clusters than requested"


# Test 9: inconsistent matrix shape and values
@given(observations(min_samples=3, max_samples=12, min_features=2, max_features=3))
def test_inconsistent_validity(obs):
    Z = hier.linkage(obs, method='average')
    R = hier.inconsistent(Z)
    
    # Should have same number of rows as Z
    assert len(R) == len(Z), f"Inconsistent matrix has {len(R)} rows, expected {len(Z)}"
    assert R.shape[1] == 4, f"Inconsistent matrix has {R.shape[1]} columns, expected 4"
    
    # Standard deviations (column 1) should be non-negative
    assert np.all(R[:, 1] >= 0), "Some standard deviations are negative"
    
    # Counts (column 2) should be positive integers
    assert np.all(R[:, 2] >= 1), "Some counts are less than 1"
    assert np.allclose(R[:, 2], R[:, 2].astype(int)), "Counts are not integers"


# Test 10: Ward linkage specific property
@given(observations(min_samples=3, max_samples=10, min_features=2, max_features=3))
def test_ward_linkage_properties(obs):
    # Ward linkage should minimize within-cluster variance
    Z = hier.linkage(obs, method='ward')
    
    # Ward should produce valid and monotonic linkage
    assert hier.is_valid_linkage(Z), "Ward linkage is not valid"
    assert hier.is_monotonic(Z), "Ward linkage is not monotonic"
    
    # Distances should increase (monotonic property specific check)
    distances = Z[:, 2]
    for i in range(1, len(distances)):
        assert distances[i] >= distances[i-1] or math.isclose(distances[i], distances[i-1], rel_tol=1e-9), \
            f"Distance decreased from {distances[i-1]} to {distances[i]}"


if __name__ == "__main__":
    print("Running scipy.cluster property-based tests...")
    pytest.main([__file__, "-v"])