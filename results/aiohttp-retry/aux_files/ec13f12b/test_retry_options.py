#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import math

from aiohttp_retry.retry_options import (
    ExponentialRetry,
    RandomRetry,
    ListRetry,
    FibonacciRetry,
    JitterRetry
)


@composite
def positive_floats(draw, min_value=0.001, max_value=1e6):
    """Generate positive floats for timeout values."""
    return draw(st.floats(min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False))


@given(
    attempts=st.integers(min_value=1, max_value=20),
    start_timeout=positive_floats(min_value=0.001, max_value=100),
    max_timeout=positive_floats(min_value=0.001, max_value=1000),
    factor=st.floats(min_value=1.1, max_value=10, allow_nan=False, allow_infinity=False),
    attempt=st.integers(min_value=0, max_value=19)
)
def test_exponential_retry_respects_max_timeout(attempts, start_timeout, max_timeout, factor, attempt):
    """Test that ExponentialRetry always respects max_timeout."""
    assume(attempt < attempts)
    
    retry = ExponentialRetry(
        attempts=attempts,
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor
    )
    
    timeout = retry.get_timeout(attempt)
    
    # Property 1: Timeout should never exceed max_timeout
    assert timeout <= max_timeout, f"Timeout {timeout} exceeds max_timeout {max_timeout}"
    
    # Property 2: Timeout should be at least start_timeout
    assert timeout >= start_timeout or timeout == max_timeout


@given(
    attempts=st.integers(min_value=1, max_value=20),
    start_timeout=positive_floats(min_value=0.001, max_value=100),
    max_timeout=positive_floats(min_value=0.001, max_value=1000),
    factor=st.floats(min_value=1.1, max_value=10, allow_nan=False, allow_infinity=False)
)
def test_exponential_retry_growth(attempts, start_timeout, max_timeout, factor):
    """Test that ExponentialRetry grows exponentially."""
    retry = ExponentialRetry(
        attempts=attempts,
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor
    )
    
    # Test monotonic growth until hitting max_timeout
    prev_timeout = 0
    for attempt in range(min(attempts, 10)):  # Test first 10 attempts
        timeout = retry.get_timeout(attempt)
        
        # Should grow monotonically (or stay at max)
        assert timeout >= prev_timeout, f"Timeout decreased from {prev_timeout} to {timeout} at attempt {attempt}"
        
        # Check exponential formula when not capped
        expected = start_timeout * (factor ** attempt)
        if expected <= max_timeout:
            assert math.isclose(timeout, expected, rel_tol=1e-9), \
                f"Expected {expected} but got {timeout} at attempt {attempt}"
        else:
            assert timeout == max_timeout
        
        prev_timeout = timeout


@given(
    min_timeout=positive_floats(min_value=0.001, max_value=100),
    max_timeout=positive_floats(min_value=0.001, max_value=1000),
    attempts=st.integers(min_value=1, max_value=100),
    attempt=st.integers(min_value=0, max_value=99)
)
def test_random_retry_bounds(min_timeout, max_timeout, attempts, attempt):
    """Test that RandomRetry always returns values within bounds."""
    assume(min_timeout <= max_timeout)
    assume(attempt < attempts)
    
    retry = RandomRetry(
        attempts=attempts,
        min_timeout=min_timeout,
        max_timeout=max_timeout
    )
    
    # Generate many samples to test bounds
    for _ in range(100):
        timeout = retry.get_timeout(attempt)
        
        # Property: timeout should always be within [min_timeout, max_timeout]
        assert min_timeout <= timeout <= max_timeout, \
            f"Timeout {timeout} not in range [{min_timeout}, {max_timeout}]"


@given(
    timeouts=st.lists(positive_floats(), min_size=1, max_size=20),
    attempt=st.integers(min_value=0, max_value=19)
)
def test_list_retry_returns_correct_timeout(timeouts, attempt):
    """Test that ListRetry returns the correct timeout from the list."""
    assume(attempt < len(timeouts))
    
    retry = ListRetry(timeouts=timeouts)
    
    # Property 1: attempts should equal length of timeouts
    assert retry.attempts == len(timeouts)
    
    # Property 2: get_timeout should return the correct value from the list
    timeout = retry.get_timeout(attempt)
    assert timeout == timeouts[attempt], \
        f"Expected timeout {timeouts[attempt]} at index {attempt}, got {timeout}"


@given(
    timeouts=st.lists(positive_floats(), min_size=1, max_size=20)
)
def test_list_retry_out_of_bounds(timeouts):
    """Test ListRetry behavior with out-of-bounds access."""
    retry = ListRetry(timeouts=timeouts)
    
    # This should raise an IndexError for invalid attempts
    try:
        # Attempt beyond the list length
        retry.get_timeout(len(timeouts))
        assert False, "Should have raised IndexError"
    except IndexError:
        pass  # Expected behavior


@given(
    attempts=st.integers(min_value=1, max_value=10),
    multiplier=st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
    max_timeout=positive_floats(min_value=1, max_value=1000)
)
def test_fibonacci_retry_respects_max_timeout(attempts, multiplier, max_timeout):
    """Test that FibonacciRetry respects max_timeout."""
    retry = FibonacciRetry(
        attempts=attempts,
        multiplier=multiplier,
        max_timeout=max_timeout
    )
    
    for attempt in range(attempts):
        timeout = retry.get_timeout(attempt)
        
        # Property: timeout should never exceed max_timeout
        assert timeout <= max_timeout, \
            f"Timeout {timeout} exceeds max_timeout {max_timeout} at attempt {attempt}"


@given(
    attempts=st.integers(min_value=3, max_value=10),
    multiplier=st.floats(min_value=0.1, max_value=2, allow_nan=False, allow_infinity=False),
    max_timeout=positive_floats(min_value=100, max_value=1000)
)
def test_fibonacci_retry_sequence(attempts, multiplier, max_timeout):
    """Test that FibonacciRetry follows Fibonacci-like sequence."""
    # Create two instances to test if they behave the same way
    retry1 = FibonacciRetry(
        attempts=attempts,
        multiplier=multiplier,
        max_timeout=max_timeout
    )
    
    retry2 = FibonacciRetry(
        attempts=attempts,
        multiplier=multiplier,
        max_timeout=max_timeout
    )
    
    # Both should produce same sequence
    for attempt in range(attempts):
        timeout1 = retry1.get_timeout(attempt)
        timeout2 = retry2.get_timeout(attempt)
        
        # Fresh instances should produce the same values
        assert math.isclose(timeout1, timeout2, rel_tol=1e-9), \
            f"Different instances produced different timeouts: {timeout1} vs {timeout2}"


@given(
    attempts=st.integers(min_value=1, max_value=10),
    multiplier=st.floats(min_value=0.5, max_value=2, allow_nan=False, allow_infinity=False),
    max_timeout=positive_floats(min_value=10, max_value=100)
)
def test_fibonacci_retry_statefulness_bug(attempts, multiplier, max_timeout):
    """Test for potential statefulness bug in FibonacciRetry."""
    retry = FibonacciRetry(
        attempts=attempts,
        multiplier=multiplier,
        max_timeout=max_timeout
    )
    
    # Get timeout for attempt 0 multiple times
    first_call = retry.get_timeout(0)
    second_call = retry.get_timeout(0)
    third_call = retry.get_timeout(0)
    
    # Property: Calling with same attempt should produce the same results
    # This tests if the implementation incorrectly maintains state between calls
    assert first_call == second_call == third_call, \
        f"FibonacciRetry appears to be stateful! Calls produced: {first_call}, {second_call}, {third_call}"


@given(
    attempts=st.integers(min_value=1, max_value=10),
    start_timeout=positive_floats(min_value=0.1, max_value=10),
    max_timeout=positive_floats(min_value=1, max_value=100),
    factor=st.floats(min_value=1.5, max_value=3, allow_nan=False, allow_infinity=False),
    random_interval_size=st.floats(min_value=0.1, max_value=5, allow_nan=False, allow_infinity=False),
    attempt=st.integers(min_value=0, max_value=9)
)
def test_jitter_retry_adds_jitter(attempts, start_timeout, max_timeout, factor, random_interval_size, attempt):
    """Test that JitterRetry adds jitter to exponential backoff."""
    assume(attempt < attempts)
    assume(start_timeout <= max_timeout)
    
    # Create base exponential retry for comparison
    base_retry = ExponentialRetry(
        attempts=attempts,
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor
    )
    
    jitter_retry = JitterRetry(
        attempts=attempts,
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor,
        random_interval_size=random_interval_size
    )
    
    base_timeout = base_retry.get_timeout(attempt)
    
    # Sample multiple times to check jitter behavior
    timeouts = [jitter_retry.get_timeout(attempt) for _ in range(20)]
    
    # Property: JitterRetry should add positive jitter to base timeout
    for timeout in timeouts:
        # Jitter should make timeout >= base_timeout
        assert timeout >= base_timeout, \
            f"Jitter timeout {timeout} less than base {base_timeout}"


if __name__ == "__main__":
    # Run a quick sanity check
    print("Running property-based tests for retry_options...")
    test_exponential_retry_respects_max_timeout()
    test_fibonacci_retry_statefulness_bug()
    print("Quick tests passed!")