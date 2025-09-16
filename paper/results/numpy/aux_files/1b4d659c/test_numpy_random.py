import numpy as np
import numpy.random
from hypothesis import given, strategies as st, assume, settings
import math
import pytest

@given(st.lists(st.integers(min_value=-1000000, max_value=1000000), min_size=1))
def test_permutation_preserves_elements(arr):
    """Permutation should preserve all elements exactly once"""
    result = numpy.random.permutation(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

@given(st.lists(st.integers(), min_size=1))
def test_permutation_idempotent_set(arr):
    """Set of permuted elements should equal original set"""
    result = numpy.random.permutation(arr)
    assert set(result) == set(arr)

@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=100),
    st.integers(min_value=1, max_value=1000)
)
def test_choice_with_replacement(arr, size):
    """Choice with replacement should only select from given elements"""
    result = numpy.random.choice(arr, size=size, replace=True)
    assert len(result) == size
    assert all(elem in arr for elem in result)

@given(
    st.lists(st.integers(), min_size=1, unique=True),
    st.data()
)
def test_choice_without_replacement(arr, data):
    """Choice without replacement should select unique elements"""
    size = data.draw(st.integers(min_value=1, max_value=len(arr)))
    result = numpy.random.choice(arr, size=size, replace=False)
    assert len(result) == size
    assert len(set(result)) == size
    assert all(elem in arr for elem in result)

@given(
    st.lists(st.floats(min_value=0.01, max_value=1000, allow_nan=False), min_size=1),
    st.data()
)  
def test_choice_with_probabilities(arr, data):
    """Choice with probabilities should respect probability constraints"""
    probs = np.array([data.draw(st.floats(min_value=0.01, max_value=1.0)) for _ in arr])
    probs = probs / probs.sum()
    
    result = numpy.random.choice(arr, size=1000, replace=True, p=probs)
    assert all(elem in arr for elem in result)

@given(st.integers(min_value=0, max_value=100))
def test_randint_single_value(high):
    """randint(0, n) should produce values in [0, n)"""
    if high == 0:
        return
    result = numpy.random.randint(high)
    assert 0 <= result < high

@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=1, max_value=1000)
)
def test_randint_range(low, diff):
    """randint(low, high) should produce values in [low, high)"""
    high = low + diff
    result = numpy.random.randint(low, high, size=100)
    assert all(low <= val < high for val in result)

@given(st.lists(st.integers(), min_size=1))
def test_shuffle_inplace_preserves_elements(arr):
    """Shuffle should preserve elements in-place"""
    original = arr.copy()
    arr_np = np.array(arr)
    numpy.random.shuffle(arr_np)
    assert len(arr_np) == len(original)
    assert sorted(arr_np) == sorted(original)

@given(st.floats(min_value=0.1, max_value=100, allow_nan=False))
def test_exponential_positive(scale):
    """Exponential distribution should produce positive values"""
    samples = numpy.random.exponential(scale, size=100)
    assert all(s >= 0 for s in samples)

@given(
    st.floats(min_value=0.1, max_value=100, allow_nan=False),
    st.floats(min_value=0.1, max_value=100, allow_nan=False)
)
def test_beta_range(a, b):
    """Beta distribution should produce values in [0, 1]"""
    samples = numpy.random.beta(a, b, size=100)
    assert all(0 <= s <= 1 for s in samples)

@given(
    st.floats(min_value=-100, max_value=100, allow_nan=False),
    st.floats(min_value=0.1, max_value=100, allow_nan=False)
)
def test_normal_symmetry(loc, scale):
    """Normal distribution should be symmetric around mean"""
    samples = numpy.random.normal(loc, scale, size=10000)
    mean = np.mean(samples)
    assert math.isclose(mean, loc, rel_tol=0.1, abs_tol=0.1)

@given(
    st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False)
)
def test_uniform_range(low, high):
    """Uniform distribution should respect bounds"""
    if low >= high:
        low, high = high, low
    if low == high:
        return
    
    samples = numpy.random.uniform(low, high, size=1000)
    assert all(low <= s <= high for s in samples)

@given(st.integers(min_value=1, max_value=100))
def test_random_range(size):
    """random() should produce values in [0, 1)"""
    samples = numpy.random.random(size)
    assert all(0 <= s < 1 for s in samples)

@given(
    st.integers(min_value=1, max_value=100),
    st.floats(min_value=0.01, max_value=0.99)
)
def test_binomial_bounds(n, p):
    """Binomial distribution should respect bounds"""
    samples = numpy.random.binomial(n, p, size=100)
    assert all(0 <= s <= n for s in samples)

@given(st.floats(min_value=0.1, max_value=100, allow_nan=False))
def test_poisson_nonnegative(lam):
    """Poisson distribution should produce non-negative integers"""
    samples = numpy.random.poisson(lam, size=100)
    assert all(s >= 0 and isinstance(s.item(), (int, np.integer)) for s in samples)

@given(st.floats(min_value=1.1, max_value=100, allow_nan=False))
def test_pareto_positive(a):
    """Pareto distribution should produce positive values"""
    samples = numpy.random.pareto(a, size=100)
    assert all(s >= 0 for s in samples)

@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=1, max_value=1000)
)
def test_hypergeometric_bounds(ngood, nbad, nsample):
    """Hypergeometric distribution should respect bounds"""
    if nsample > ngood + nbad:
        return
    
    samples = numpy.random.hypergeometric(ngood, nbad, nsample, size=100)
    assert all(0 <= s <= min(ngood, nsample) for s in samples)

@given(st.floats(min_value=0.1, max_value=100, allow_nan=False))
def test_rayleigh_positive(scale):
    """Rayleigh distribution should produce positive values"""
    samples = numpy.random.rayleigh(scale, size=100)
    assert all(s >= 0 for s in samples)

@given(st.lists(st.floats(min_value=0.01, max_value=100, allow_nan=False), min_size=2))
def test_dirichlet_sums_to_one(alpha):
    """Dirichlet distribution samples should sum to 1"""
    samples = numpy.random.dirichlet(alpha, size=100)
    for sample in samples:
        assert math.isclose(sum(sample), 1.0, rel_tol=1e-7)
        assert all(0 <= s <= 1 for s in sample)

@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=100)
)
def test_multinomial_sum(n, k):
    """Multinomial samples should sum to n"""
    pvals = numpy.random.random(k)
    pvals = pvals / pvals.sum()
    
    samples = numpy.random.multinomial(n, pvals, size=100)
    for sample in samples:
        assert sum(sample) == n
        assert all(s >= 0 for s in sample)

@given(st.integers(min_value=1, max_value=1000000))
def test_seed_deterministic(seed):
    """Setting seed should produce deterministic results"""
    numpy.random.seed(seed)
    result1 = numpy.random.random(10)
    
    numpy.random.seed(seed)
    result2 = numpy.random.random(10)
    
    assert np.array_equal(result1, result2)

@given(
    st.lists(st.integers(), min_size=2, max_size=100),
    st.integers(min_value=0)
)
def test_permutation_with_seed(arr, seed):
    """Permutation with same seed should be deterministic"""
    numpy.random.seed(seed)
    perm1 = numpy.random.permutation(arr)
    
    numpy.random.seed(seed)
    perm2 = numpy.random.permutation(arr)
    
    assert np.array_equal(perm1, perm2)

@given(st.integers(min_value=1, max_value=100))
def test_bytes_length(nbytes):
    """bytes should return exactly nbytes bytes"""
    result = numpy.random.bytes(nbytes)
    assert len(result) == nbytes
    assert isinstance(result, bytes)

@given(
    st.floats(min_value=0.1, max_value=10, allow_nan=False),
    st.floats(min_value=0.1, max_value=10, allow_nan=False)
)
def test_gamma_positive(shape, scale):
    """Gamma distribution should produce positive values"""
    samples = numpy.random.gamma(shape, scale, size=100)
    assert all(s >= 0 for s in samples)

@given(st.floats(min_value=0.01, max_value=0.99))
def test_geometric_positive_integer(p):
    """Geometric distribution should produce positive integers"""
    samples = numpy.random.geometric(p, size=100)
    assert all(s >= 1 and isinstance(s.item(), (int, np.integer)) for s in samples)

@given(
    st.floats(min_value=-100, max_value=100, allow_nan=False),
    st.floats(min_value=0.1, max_value=100, allow_nan=False)
)
def test_laplace_median(loc, scale):
    """Laplace distribution median should be loc"""
    samples = numpy.random.laplace(loc, scale, size=10000)
    median = np.median(samples)
    assert math.isclose(median, loc, rel_tol=0.1, abs_tol=0.1)

@given(st.floats(min_value=-3.14, max_value=3.14, allow_nan=False))
def test_vonmises_range(mu):
    """Von Mises distribution should produce values in [-pi, pi]"""
    kappa = 1.0
    samples = numpy.random.vonmises(mu, kappa, size=100)
    assert all(-math.pi <= s <= math.pi for s in samples)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])