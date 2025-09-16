import numpy as np
import numpy.random
from hypothesis import given, strategies as st, assume, settings
import math
import pytest

@given(st.integers())
def test_seed_value_range(seed):
    """Seed should handle values in [0, 2**32 - 1]"""
    if 0 <= seed <= 2**32 - 1:
        numpy.random.seed(seed)
    else:
        with pytest.raises(ValueError, match="Seed must be between 0 and 2\\*\\*32 - 1"):
            numpy.random.seed(seed)

@given(st.lists(st.just(0), min_size=1))
def test_permutation_all_zeros(arr):
    """Permutation of identical elements should work"""
    result = numpy.random.permutation(arr)
    assert len(result) == len(arr)
    assert all(x == 0 for x in result)

@given(st.just([]))
def test_permutation_empty(arr):
    """Permutation of empty list should return empty"""
    result = numpy.random.permutation(arr)
    assert len(result) == 0

@given(st.lists(st.integers(), min_size=0, max_size=0))
def test_shuffle_empty(arr):
    """Shuffle of empty array should work"""
    arr_np = np.array(arr)
    numpy.random.shuffle(arr_np)
    assert len(arr_np) == 0

@given(st.just([]))
def test_choice_empty(arr):
    """Choice from empty array should raise error"""
    with pytest.raises(ValueError):
        numpy.random.choice(arr)

@given(st.lists(st.integers(), min_size=1))
def test_choice_size_zero(arr):
    """Choice with size=0 should return empty array"""
    result = numpy.random.choice(arr, size=0)
    assert len(result) == 0

@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_choice_larger_size_without_replacement(arr):
    """Choice without replacement with size > len(arr) should fail"""
    with pytest.raises(ValueError):
        numpy.random.choice(arr, size=len(arr) + 1, replace=False)

@given(st.integers(min_value=-1000, max_value=-1))
def test_randint_negative_high(high):
    """randint with negative high should fail"""
    with pytest.raises(ValueError):
        numpy.random.randint(high)

@given(st.integers())
def test_randint_low_equals_high(val):
    """randint with low == high should fail"""
    with pytest.raises(ValueError):
        numpy.random.randint(val, val)

@given(st.integers(min_value=1, max_value=1000))
def test_randint_low_greater_than_high(diff):
    """randint with low > high should fail"""
    low = 100
    high = low - diff
    with pytest.raises(ValueError):
        numpy.random.randint(low, high)

@given(st.floats(allow_nan=True, allow_infinity=False))
def test_exponential_with_nan(scale):
    """Exponential with NaN scale should handle gracefully"""
    if math.isnan(scale):
        result = numpy.random.exponential(scale)
        assert math.isnan(result)
    elif scale <= 0:
        with pytest.raises(ValueError):
            numpy.random.exponential(scale)
    else:
        result = numpy.random.exponential(scale)
        assert result >= 0

@given(st.floats(allow_infinity=True, allow_nan=False))
def test_normal_with_infinity(scale):
    """Normal with infinite scale"""
    if math.isinf(scale):
        if scale > 0:
            result = numpy.random.normal(0, scale)
        else:
            with pytest.raises(ValueError):
                numpy.random.normal(0, scale)
    elif scale <= 0:
        with pytest.raises(ValueError):
            numpy.random.normal(0, scale)
    else:
        result = numpy.random.normal(0, scale)

@given(
    st.lists(st.floats(min_value=1e-10, max_value=1.0), min_size=2),
    st.integers(min_value=1, max_value=100)
)
def test_choice_probabilities_normalization(values, size):
    """Choice should normalize probabilities automatically"""
    probs = np.random.random(len(values))
    result = numpy.random.choice(values, size=size, p=probs/probs.sum())
    assert all(r in values for r in result)

@given(st.lists(st.integers(), min_size=2))
def test_choice_negative_probabilities(arr):
    """Choice with negative probabilities should fail"""
    probs = [-0.1] + [0.1] * (len(arr) - 1)
    with pytest.raises(ValueError):
        numpy.random.choice(arr, p=probs)

@given(st.lists(st.integers(), min_size=2))
def test_choice_probabilities_wrong_sum(arr):
    """Choice with probabilities not summing to 1 should fail if not close"""
    probs = [0.1] * len(arr)
    with pytest.raises(ValueError):
        numpy.random.choice(arr, p=probs)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])