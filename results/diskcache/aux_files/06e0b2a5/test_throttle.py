import math
import time
import tempfile
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import diskcache from the virtual environment
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')
import diskcache
from diskcache.recipes import throttle


# Test throttle rate limiting property
@given(
    st.integers(min_value=2, max_value=10),  # count (calls allowed)
    st.floats(min_value=0.1, max_value=1.0),  # seconds (time period)
)
@settings(deadline=5000, max_examples=20)
def test_throttle_rate_limiting(count, seconds):
    """Test that throttle correctly limits the rate of function calls."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        call_times = []
        
        @throttle(cache, count, seconds)
        def rate_limited_func():
            call_times.append(time.time())
        
        # Try to call the function more times than allowed
        start_time = time.time()
        attempts = count * 2
        
        for _ in range(attempts):
            rate_limited_func()
        
        elapsed = time.time() - start_time
        
        # We should have been throttled, so elapsed time should be at least seconds
        # (since we're trying to call 2x the allowed rate)
        # Allow some tolerance for timing
        assert elapsed >= seconds * 0.8  # Allow 20% tolerance
        
        # Check that we made the expected number of calls in the first period
        # Count calls in first "seconds" period
        first_period_calls = sum(1 for t in call_times if t - start_time <= seconds * 1.1)
        
        # Should be approximately count calls (with some tolerance)
        assert first_period_calls <= count + 1  # Allow one extra due to timing


# Test that throttle maintains state across calls
def test_throttle_maintains_state():
    """Test that throttle maintains its state correctly across multiple calls."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        counter = 0
        
        @throttle(cache, 2, 0.5)  # 2 calls per 0.5 seconds
        def increment():
            nonlocal counter
            counter += 1
        
        # First two calls should be immediate
        start = time.time()
        increment()
        increment()
        time_after_two = time.time() - start
        
        # Should be very quick (< 0.1 seconds)
        assert time_after_two < 0.1
        assert counter == 2
        
        # Third call should be delayed
        increment()
        time_after_three = time.time() - start
        
        # Should have waited approximately 0.5 seconds
        assert time_after_three >= 0.4  # Allow some tolerance
        assert counter == 3


# Test throttle with custom time functions
@given(st.integers(min_value=1, max_value=5))
def test_throttle_custom_time_functions(count):
    """Test throttle with custom time and sleep functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        # Create mock time that advances in fixed increments
        mock_time = 0.0
        sleep_total = 0.0
        
        def mock_time_func():
            return mock_time
        
        def mock_sleep_func(duration):
            nonlocal mock_time, sleep_total
            mock_time += duration
            sleep_total += duration
        
        calls = 0
        
        @throttle(cache, count, 1.0, time_func=mock_time_func, sleep_func=mock_sleep_func)
        def test_func():
            nonlocal calls
            calls += 1
        
        # Call function count times (should all succeed immediately)
        for _ in range(count):
            test_func()
        
        assert calls == count
        assert sleep_total == 0  # No sleeping needed for first 'count' calls
        
        # Next call should require sleep
        test_func()
        assert sleep_total > 0  # Should have slept
        assert calls == count + 1


# Test throttle with zero seconds (edge case)
def test_throttle_zero_seconds():
    """Test throttle with seconds=0 - should effectively disable throttling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        # This is an edge case - what happens with 0 seconds?
        # Based on the code, rate = count / float(seconds), so this would be division by zero
        with pytest.raises(ZeroDivisionError):
            @throttle(cache, 5, 0)
            def func():
                pass


# Test multiple throttled functions don't interfere
def test_throttle_function_independence():
    """Test that multiple throttled functions maintain independent rate limits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        counter1 = 0
        counter2 = 0
        
        @throttle(cache, 2, 0.5, name='func1')
        def func1():
            nonlocal counter1
            counter1 += 1
        
        @throttle(cache, 3, 0.5, name='func2')
        def func2():
            nonlocal counter2
            counter2 += 1
        
        # Call each function its limit number of times
        start = time.time()
        func1()
        func1()
        func2()
        func2()
        func2()
        elapsed = time.time() - start
        
        # All should complete quickly since they're within limits
        assert elapsed < 0.1
        assert counter1 == 2
        assert counter2 == 3
        
        # Now exceeding limit on func1 should delay, but func2 should still work
        func1()  # This should delay
        elapsed_func1 = time.time() - start
        assert elapsed_func1 >= 0.4  # Should have waited
        
        # func2 can still be called immediately (it has its own limit)
        # But we already used up its quota, so it will also delay
        start2 = time.time()
        func2()
        elapsed_func2 = time.time() - start2
        assert elapsed_func2 >= 0.3  # Should have waited


# Test throttle with negative count (invalid input)
def test_throttle_negative_count():
    """Test throttle with negative count - tests input validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        # Negative count doesn't make sense
        # The code calculates rate = count / float(seconds)
        # With negative count, rate would be negative
        @throttle(cache, -5, 1.0)
        def func():
            return "called"
        
        # This might behave unexpectedly - let's see what happens
        # Based on the logic, negative rate means tally will decrease instead of increase
        # This could lead to infinite calls without throttling
        start = time.time()
        for _ in range(10):
            result = func()
            assert result == "called"
        elapsed = time.time() - start
        
        # With negative count, the throttling logic breaks down
        # All calls should complete immediately (no throttling)
        assert elapsed < 0.5  # Should be fast, no throttling