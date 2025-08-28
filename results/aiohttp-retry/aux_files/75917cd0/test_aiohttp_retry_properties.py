#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, settings, assume

from aiohttp_retry.retry_options import (
    ExponentialRetry, ListRetry, FibonacciRetry, JitterRetry, RandomRetry
)


@given(
    timeouts=st.lists(st.floats(min_value=0.0, max_value=100.0), min_size=1, max_size=10),
    attempt=st.integers(min_value=0, max_value=20)
)
def test_listretry_index_bounds(timeouts, attempt):
    """Test that ListRetry.get_timeout handles attempt indices correctly.
    
    The code at line 148 uses self.timeouts[attempt] which could be out of bounds
    since attempt is 0-based but could exceed len(timeouts)-1.
    """
    retry = ListRetry(timeouts=timeouts)
    
    # The attempts property is set to len(timeouts)
    assert retry.attempts == len(timeouts)
    
    # If attempt is within bounds, it should work
    if attempt < len(timeouts):
        timeout = retry.get_timeout(attempt)
        assert timeout == timeouts[attempt]
    else:
        # If attempt is out of bounds, it should raise IndexError
        try:
            timeout = retry.get_timeout(attempt)
            # If we get here, there's a bug - it should have raised
            assert False, f"Expected IndexError for attempt={attempt}, len(timeouts)={len(timeouts)}"
        except IndexError:
            pass  # Expected behavior


@given(
    attempts=st.integers(min_value=1, max_value=10),
    multiplier=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    max_timeout=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
)
def test_fibonacci_retry_state_mutation(attempts, multiplier, max_timeout):
    """Test that FibonacciRetry properly maintains state across multiple calls.
    
    The FibonacciRetry class mutates its internal state, which could lead to
    incorrect behavior when the same instance is reused.
    """
    retry = FibonacciRetry(attempts=attempts, multiplier=multiplier, max_timeout=max_timeout)
    
    # Get timeouts for all attempts
    timeouts1 = []
    for i in range(attempts):
        timeout = retry.get_timeout(i)
        timeouts1.append(timeout)
        assert timeout <= max_timeout, f"Timeout {timeout} exceeds max_timeout {max_timeout}"
    
    # Create a new instance and get timeouts again
    retry2 = FibonacciRetry(attempts=attempts, multiplier=multiplier, max_timeout=max_timeout)
    timeouts2 = []
    for i in range(attempts):
        timeout = retry2.get_timeout(i)
        timeouts2.append(timeout)
    
    # The timeouts should follow Fibonacci pattern
    # First timeout should be multiplier * 2 (fib(2) = 1+1 = 2)
    expected_first = min(multiplier * 2.0, max_timeout)
    assert math.isclose(timeouts1[0], expected_first, rel_tol=1e-9)
    
    # Check if continuing to call get_timeout on the same instance causes issues
    # Since state is mutated, calling again should give different results
    timeout_reused = retry.get_timeout(0)
    # This should be different from the first call since state has changed
    assert not math.isclose(timeout_reused, timeouts1[0], rel_tol=1e-9)


@given(
    attempts=st.integers(min_value=1, max_value=10),
    start_timeout=st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False),
    max_timeout=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    factor=st.floats(min_value=1.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_exponential_retry_bounds(attempts, start_timeout, max_timeout, factor):
    """Test that ExponentialRetry respects timeout bounds.
    
    The timeout should grow exponentially but never exceed max_timeout.
    """
    assume(max_timeout > start_timeout)
    
    retry = ExponentialRetry(
        attempts=attempts,
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor
    )
    
    prev_timeout = 0
    for attempt in range(attempts):
        timeout = retry.get_timeout(attempt)
        
        # Timeout should be positive
        assert timeout > 0
        
        # Timeout should not exceed max_timeout
        assert timeout <= max_timeout
        
        # For attempt 0, timeout should be start_timeout
        if attempt == 0:
            expected = start_timeout * (factor ** attempt)
            assert math.isclose(timeout, min(expected, max_timeout), rel_tol=1e-9)
        
        # Timeout should grow (or stay at max) with each attempt
        if attempt > 0:
            assert timeout >= prev_timeout or math.isclose(timeout, max_timeout, rel_tol=1e-9)
        
        prev_timeout = timeout


@given(
    attempts=st.integers(min_value=1, max_value=10),
    start_timeout=st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False),
    max_timeout=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    factor=st.floats(min_value=1.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    random_interval_size=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_jitter_retry_respects_bounds(attempts, start_timeout, max_timeout, factor, random_interval_size):
    """Test that JitterRetry adds jitter but may exceed max_timeout.
    
    JitterRetry adds random jitter on top of exponential backoff.
    Looking at line 227, it adds random.uniform(0, random_interval_size) ** factor
    to the base timeout, which could make the final timeout exceed max_timeout.
    """
    assume(max_timeout > start_timeout)
    
    retry = JitterRetry(
        attempts=attempts,
        start_timeout=start_timeout,
        max_timeout=max_timeout,
        factor=factor,
        random_interval_size=random_interval_size
    )
    
    # Run multiple times to account for randomness
    for _ in range(10):
        for attempt in range(attempts):
            timeout = retry.get_timeout(attempt)
            
            # Timeout should be positive
            assert timeout > 0
            
            # Get the base exponential timeout
            base_timeout = start_timeout * (factor ** attempt)
            capped_base = min(base_timeout, max_timeout)
            
            # The jitter adds: random.uniform(0, random_interval_size) ** factor
            # Maximum possible jitter is random_interval_size ** factor
            max_jitter = random_interval_size ** factor
            
            # The actual timeout could exceed max_timeout due to jitter!
            # This might be a bug - the jitter is added AFTER capping to max_timeout
            max_possible_timeout = capped_base + max_jitter
            
            # Check if timeout can exceed the intended max_timeout
            if timeout > max_timeout:
                print(f"BUG: JitterRetry timeout {timeout} exceeds max_timeout {max_timeout}")
                print(f"  attempt={attempt}, base={capped_base}, max_jitter={max_jitter}")
                # This is likely a bug - timeout exceeds max_timeout
                assert timeout <= max_possible_timeout  # Should at least be bounded by this


@given(
    min_timeout=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    max_timeout=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_random_retry_bounds(min_timeout, max_timeout):
    """Test that RandomRetry respects timeout bounds."""
    assume(max_timeout > min_timeout)
    
    retry = RandomRetry(
        attempts=5,
        min_timeout=min_timeout,
        max_timeout=max_timeout
    )
    
    for attempt in range(10):  # Test multiple attempts
        timeout = retry.get_timeout(attempt)
        assert min_timeout <= timeout <= max_timeout


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])