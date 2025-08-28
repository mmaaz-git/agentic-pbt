#!/usr/bin/env /root/hypothesis-llm/envs/aiohttp-retry_env/bin/python3
"""Property-based tests for aiohttp_retry.client module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from aiohttp_retry.client import _url_to_urls
from aiohttp_retry.retry_options import (
    ExponentialRetry, RandomRetry, ListRetry, FibonacciRetry, JitterRetry
)
from yarl import URL

# Test 1: URL conversion invariants
@given(st.text(min_size=1))
def test_url_string_conversion(url_str):
    """Strings should become single-element tuples."""
    result = _url_to_urls(url_str)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == url_str


@given(st.lists(st.text(min_size=1), min_size=1))
def test_url_list_conversion(url_list):
    """Lists should be converted to tuples with same elements."""
    result = _url_to_urls(url_list)
    assert isinstance(result, tuple)
    assert len(result) == len(url_list)
    assert all(r == u for r, u in zip(result, url_list))


@given(st.lists(st.text(min_size=1), max_size=0))
def test_empty_list_raises_error(empty_list):
    """Empty lists should raise ValueError."""
    with pytest.raises(ValueError) as exc:
        _url_to_urls(empty_list)
    assert "you can pass url by str or list/tuple with attempts count size" in str(exc.value)


# Test 2: ExponentialRetry timeout bounds
@given(
    st.integers(min_value=0, max_value=10),
    st.floats(min_value=0.001, max_value=1.0),
    st.floats(min_value=1.0, max_value=100.0),
    st.floats(min_value=1.1, max_value=10.0)
)
def test_exponential_retry_bounds(attempt, start_timeout, max_timeout, factor):
    """Exponential retry timeout should be within bounds."""
    retry = ExponentialRetry(
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor
    )
    timeout = retry.get_timeout(attempt)
    assert timeout >= start_timeout
    assert timeout <= max_timeout


@given(
    st.integers(min_value=0, max_value=20),
    st.floats(min_value=0.001, max_value=1.0),
    st.floats(min_value=1.0, max_value=100.0)
)
def test_exponential_retry_growth(attempt, start_timeout, max_timeout):
    """Exponential retry should grow with default factor of 2."""
    retry = ExponentialRetry(
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=2.0
    )
    timeout = retry.get_timeout(attempt)
    expected = start_timeout * (2.0 ** attempt)
    assert timeout == min(expected, max_timeout)


# Test 3: RandomRetry timeout bounds
@given(
    st.integers(min_value=0, max_value=100),
    st.floats(min_value=0.001, max_value=10.0),
    st.floats(min_value=10.001, max_value=100.0)
)
def test_random_retry_bounds(attempt, min_timeout, max_timeout):
    """Random retry timeout should be within specified bounds."""
    retry = RandomRetry(
        min_timeout=min_timeout,
        max_timeout=max_timeout
    )
    timeout = retry.get_timeout(attempt)
    assert timeout >= min_timeout
    assert timeout <= max_timeout


# Test 4: ListRetry indexing behavior
@given(st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=1, max_size=10))
def test_list_retry_indexing(timeouts):
    """ListRetry should use exact timeout values from list."""
    retry = ListRetry(timeouts=timeouts)
    assert retry.attempts == len(timeouts)
    for i in range(len(timeouts)):
        assert retry.get_timeout(i) == timeouts[i]


@given(
    st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=1, max_size=10),
    st.integers()
)
def test_list_retry_out_of_bounds(timeouts, index):
    """ListRetry should raise IndexError for out-of-bounds indices."""
    assume(index >= len(timeouts) or index < -len(timeouts) - 1)
    retry = ListRetry(timeouts=timeouts)
    with pytest.raises(IndexError):
        retry.get_timeout(index)


# Test 5: FibonacciRetry sequence property
@given(
    st.floats(min_value=0.1, max_value=10.0),
    st.floats(min_value=10.0, max_value=100.0)
)
def test_fibonacci_retry_sequence(multiplier, max_timeout):
    """FibonacciRetry should follow Fibonacci sequence pattern."""
    retry = FibonacciRetry(multiplier=multiplier, max_timeout=max_timeout)
    
    # Get first few timeouts
    timeouts = []
    for i in range(5):
        timeout = retry.get_timeout(i)
        timeouts.append(timeout)
        assert timeout <= max_timeout
    
    # The raw Fibonacci values before multiplier/cap
    expected_fib = [1, 2, 3, 5, 8]
    for i, (actual, fib) in enumerate(zip(timeouts, expected_fib)):
        expected = min(multiplier * fib, max_timeout)
        assert actual == expected


# Test 6: FibonacciRetry state mutation
@given(st.floats(min_value=0.1, max_value=10.0))
def test_fibonacci_retry_state_mutation(multiplier):
    """FibonacciRetry modifies internal state on each call."""
    retry = FibonacciRetry(multiplier=multiplier, max_timeout=100.0)
    
    # First sequence
    first_seq = [retry.get_timeout(i) for i in range(3)]
    
    # Reset by creating new instance
    retry2 = FibonacciRetry(multiplier=multiplier, max_timeout=100.0)
    
    # Second sequence should match first
    second_seq = [retry2.get_timeout(i) for i in range(3)]
    
    # But continuing with first instance should give different values
    # because internal state was mutated
    third_val = retry.get_timeout(3)
    retry3 = FibonacciRetry(multiplier=multiplier, max_timeout=100.0)
    _ = [retry3.get_timeout(i) for i in range(3)]
    fourth_val = retry3.get_timeout(3)
    
    assert first_seq == second_seq
    assert third_val != first_seq[0]  # State has advanced


# Test 7: JitterRetry adds positive jitter
@given(
    st.integers(min_value=0, max_value=10),
    st.floats(min_value=0.001, max_value=1.0),
    st.floats(min_value=1.0, max_value=100.0),
    st.floats(min_value=1.1, max_value=5.0),
    st.floats(min_value=0.1, max_value=5.0)
)
@settings(max_examples=200)
def test_jitter_retry_adds_jitter(attempt, start_timeout, max_timeout, factor, random_interval_size):
    """JitterRetry should add jitter on top of exponential backoff."""
    base_retry = ExponentialRetry(
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor
    )
    jitter_retry = JitterRetry(
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor,
        random_interval_size=random_interval_size
    )
    
    base_timeout = base_retry.get_timeout(attempt)
    jitter_timeout = jitter_retry.get_timeout(attempt)
    
    # Jitter should add a positive value
    assert jitter_timeout >= base_timeout
    # But the added jitter should be bounded
    max_added = random_interval_size ** factor
    assert jitter_timeout <= base_timeout + max_added


# Test 8: URL types handling
@given(st.one_of(
    st.text(min_size=1),
    st.lists(st.text(min_size=1), min_size=1),
    st.tuples(st.text(min_size=1))
))
def test_url_types_accepted(url):
    """Should accept strings, lists, and tuples."""
    result = _url_to_urls(url)
    assert isinstance(result, tuple)
    assert len(result) > 0


# Test 9: YARL URL support
def test_yarl_url_support():
    """Should support YARL URL objects."""
    yarl_url = URL("https://example.com")
    result = _url_to_urls(yarl_url)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == yarl_url


# Test 10: Invalid input types
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.dictionaries(st.text(), st.text()),
    st.none()
))
def test_invalid_url_types_raise_error(invalid_url):
    """Should raise error for invalid URL types."""
    with pytest.raises((ValueError, TypeError, AttributeError)):
        _url_to_urls(invalid_url)