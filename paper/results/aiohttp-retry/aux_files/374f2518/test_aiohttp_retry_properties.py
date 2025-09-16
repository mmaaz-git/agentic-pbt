import math
import random
from typing import List, Tuple, Union

import pytest
from aiohttp import ClientSession
from hypothesis import assume, given, settings, strategies as st
from yarl import URL as YARL_URL

# Import the modules we're testing
from aiohttp_retry.client import _url_to_urls, RetryClient
from aiohttp_retry.retry_options import (
    ExponentialRetry,
    FibonacciRetry,
    JitterRetry,
    ListRetry,
    RandomRetry,
)


# Test _url_to_urls function properties
@given(st.text(min_size=1))
def test_url_to_urls_string_returns_single_tuple(url_str):
    """String input should always return a single-element tuple."""
    result = _url_to_urls(url_str)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == url_str


@given(st.lists(st.text(min_size=1), min_size=1))
def test_url_to_urls_list_preserves_elements(url_list):
    """List input should preserve all elements in tuple form."""
    result = _url_to_urls(url_list)
    assert isinstance(result, tuple)
    assert len(result) == len(url_list)
    assert list(result) == url_list


@given(st.lists(st.text(), min_size=0, max_size=0))
def test_url_to_urls_empty_list_raises_error(empty_list):
    """Empty list should raise ValueError."""
    with pytest.raises(ValueError):
        _url_to_urls(empty_list)


@given(st.tuples())
def test_url_to_urls_empty_tuple_raises_error():
    """Empty tuple should raise ValueError."""
    with pytest.raises(ValueError):
        _url_to_urls(())


# Test ExponentialRetry timeout properties
@given(
    st.integers(min_value=0, max_value=10),
    st.floats(min_value=0.001, max_value=1.0),
    st.floats(min_value=1.0, max_value=100.0),
    st.floats(min_value=1.1, max_value=10.0),
)
def test_exponential_retry_timeout_bounded(attempt, start_timeout, max_timeout, factor):
    """ExponentialRetry timeout should never exceed max_timeout."""
    retry = ExponentialRetry(start_timeout=start_timeout, max_timeout=max_timeout, factor=factor)
    timeout = retry.get_timeout(attempt)
    
    assert timeout <= max_timeout
    assert timeout >= 0
    
    # Verify exponential formula
    expected = start_timeout * (factor ** attempt)
    assert math.isclose(timeout, min(expected, max_timeout))


@given(
    st.integers(min_value=0, max_value=10),
    st.floats(min_value=0.001, max_value=1.0),
    st.floats(min_value=1.0, max_value=100.0),
)
def test_exponential_retry_monotonic_increasing(attempt1, start_timeout, max_timeout):
    """For factor > 1, timeout should increase with attempt number until max_timeout."""
    factor = 2.0
    retry = ExponentialRetry(start_timeout=start_timeout, max_timeout=max_timeout, factor=factor)
    
    attempt2 = attempt1 + 1
    timeout1 = retry.get_timeout(attempt1)
    timeout2 = retry.get_timeout(attempt2)
    
    # Timeout should increase or stay at max
    if timeout1 < max_timeout:
        assert timeout2 >= timeout1


# Test RandomRetry timeout bounds
@given(
    st.integers(min_value=0, max_value=100),
    st.floats(min_value=0.001, max_value=10.0),
    st.floats(min_value=10.1, max_value=100.0),
)
def test_random_retry_timeout_within_bounds(attempt, min_timeout, max_timeout):
    """RandomRetry should always return timeout within specified bounds."""
    retry = RandomRetry(min_timeout=min_timeout, max_timeout=max_timeout)
    timeout = retry.get_timeout(attempt)
    
    assert min_timeout <= timeout <= max_timeout


@given(st.floats(min_value=0.001, max_value=100.0))
def test_random_retry_equal_bounds(timeout_value):
    """When min and max are equal, RandomRetry should return that exact value."""
    retry = RandomRetry(min_timeout=timeout_value, max_timeout=timeout_value)
    
    for attempt in range(5):
        result = retry.get_timeout(attempt)
        assert math.isclose(result, timeout_value)


# Test ListRetry properties
@given(st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=1, max_size=10))
def test_list_retry_attempts_equals_timeouts_length(timeouts):
    """ListRetry attempts should equal the length of timeouts list."""
    retry = ListRetry(timeouts=timeouts)
    assert retry.attempts == len(timeouts)


@given(
    st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=1, max_size=10),
    st.data(),
)
def test_list_retry_returns_correct_timeout(timeouts, data):
    """ListRetry should return the timeout at the correct index."""
    retry = ListRetry(timeouts=timeouts)
    
    # Generate valid index
    index = data.draw(st.integers(min_value=0, max_value=len(timeouts) - 1))
    timeout = retry.get_timeout(index)
    
    assert math.isclose(timeout, timeouts[index])


# Test FibonacciRetry properties
@given(
    st.floats(min_value=0.1, max_value=10.0),
    st.floats(min_value=10.1, max_value=100.0),
)
def test_fibonacci_retry_bounded(multiplier, max_timeout):
    """FibonacciRetry should never exceed max_timeout."""
    retry = FibonacciRetry(multiplier=multiplier, max_timeout=max_timeout)
    
    for attempt in range(10):
        timeout = retry.get_timeout(attempt)
        assert timeout <= max_timeout
        assert timeout >= 0


def test_fibonacci_retry_sequence():
    """FibonacciRetry should follow Fibonacci sequence pattern."""
    retry = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)
    
    # Get first few timeouts
    timeouts = []
    for i in range(6):
        timeouts.append(retry.get_timeout(i))
    
    # Verify Fibonacci relationship (after first two)
    # Each timeout should be sum of previous two (times multiplier)
    expected_fib = [1, 2, 3, 5, 8, 13]
    for i, expected in enumerate(expected_fib):
        assert math.isclose(timeouts[i], expected, rel_tol=0.01)


@given(st.floats(min_value=0.1, max_value=100.0))
def test_fibonacci_retry_multiplier_effect(multiplier):
    """FibonacciRetry multiplier should scale all timeouts proportionally."""
    retry1 = FibonacciRetry(multiplier=1.0, max_timeout=10000.0)
    retry2 = FibonacciRetry(multiplier=multiplier, max_timeout=10000.0)
    
    # Get timeout from fresh instances
    timeout1 = retry1.get_timeout(0)
    timeout2 = retry2.get_timeout(0)
    
    assert math.isclose(timeout2, timeout1 * multiplier)


# Test JitterRetry properties
@given(
    st.integers(min_value=0, max_value=10),
    st.floats(min_value=0.001, max_value=1.0),
    st.floats(min_value=1.0, max_value=100.0),
    st.floats(min_value=1.1, max_value=3.0),
    st.floats(min_value=0.1, max_value=5.0),
)
def test_jitter_retry_greater_than_base(attempt, start_timeout, max_timeout, factor, random_interval):
    """JitterRetry should always return timeout >= base exponential timeout."""
    retry = JitterRetry(
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor,
        random_interval_size=random_interval,
    )
    
    # Get base exponential timeout
    base_retry = ExponentialRetry(
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor,
    )
    base_timeout = base_retry.get_timeout(attempt)
    
    # JitterRetry should be at least as large
    jitter_timeout = retry.get_timeout(attempt)
    assert jitter_timeout >= base_timeout or math.isclose(jitter_timeout, base_timeout, rel_tol=0.01)


# Test for potential stateful bugs in FibonacciRetry
def test_fibonacci_retry_state_pollution():
    """Multiple calls to same FibonacciRetry instance should maintain correct state."""
    retry = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)
    
    # First sequence
    first_sequence = []
    for i in range(5):
        first_sequence.append(retry.get_timeout(i))
    
    # The state should have changed - verify it continues the sequence
    next_timeout = retry.get_timeout(5)
    
    # This should be the 6th Fibonacci number (starting from 1,1)
    # The sequence goes: 1, 2, 3, 5, 8, 13, 21, 34...
    # After 5 calls we've seen: 1, 2, 3, 5, 8
    # The 6th should be 13
    assert math.isclose(next_timeout, 13.0, rel_tol=0.01)


# Test edge cases for methods parameter
@given(st.sets(st.text(min_size=1, max_size=10)))
def test_retry_options_methods_uppercase(methods_set):
    """RetryOptionsBase should convert all methods to uppercase."""
    retry = ExponentialRetry(methods=methods_set)
    
    for method in retry.methods:
        assert method == method.upper()


# Test that URL can be a YARL URL object
def test_url_to_urls_yarl_url():
    """YARL URL objects should be handled correctly."""
    yarl_url = YARL_URL("http://example.com")
    result = _url_to_urls(yarl_url)
    
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == yarl_url