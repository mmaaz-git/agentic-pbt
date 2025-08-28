import math
import os
import tempfile
import threading
import time
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import diskcache from the virtual environment
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')
import diskcache
from diskcache.recipes import Averager, RLock, BoundedSemaphore, Lock, throttle


# Edge case 1: Test Averager with extreme floating point values
@given(st.lists(
    st.one_of(
        st.floats(min_value=1e300, max_value=1e308),  # Very large values
        st.floats(min_value=-1e308, max_value=-1e300),  # Very large negative
        st.floats(min_value=-1e-300, max_value=1e-300, exclude_min=True, exclude_max=True),  # Very small
    ),
    min_size=2
))
def test_averager_extreme_floats(values):
    """Test Averager with extreme floating point values that might cause overflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave = Averager(cache, 'test_key')
        
        # Filter out zeros to avoid division issues
        values = [v for v in values if v != 0]
        assume(len(values) > 0)
        
        for value in values:
            ave.add(value)
        
        result = ave.get()
        
        # Check if the result is finite
        if all(math.isfinite(v) for v in values):
            expected_sum = sum(values)
            if math.isfinite(expected_sum):
                expected = expected_sum / len(values)
                if math.isfinite(expected):
                    assert result is not None
                    # Use a more lenient comparison for extreme values
                    if abs(expected) > 1e100:
                        # For very large values, check relative error
                        assert abs((result - expected) / expected) < 1e-7
                    elif abs(expected) < 1e-100 and expected != 0:
                        # For very small values, check relative error
                        assert abs((result - expected) / expected) < 1e-7
                    else:
                        assert math.isclose(result, expected, rel_tol=1e-9)


# Edge case 2: Test Lock with rapid acquire/release cycles
@given(st.integers(min_value=10, max_value=50))
@settings(deadline=5000)  # Allow more time for this test
def test_lock_rapid_cycles(cycles):
    """Test Lock with rapid acquire/release cycles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        lock = Lock(cache, 'stress_lock')
        
        for _ in range(cycles):
            lock.acquire()
            assert lock.locked()
            lock.release()
            assert not lock.locked()


# Edge case 3: Test RLock with maximum nesting
@given(st.integers(min_value=50, max_value=100))
@settings(deadline=10000)
def test_rlock_deep_nesting(depth):
    """Test RLock with deep nesting levels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        rlock = RLock(cache, 'deep_lock')
        
        # Acquire lock 'depth' times
        for i in range(depth):
            rlock.acquire()
        
        # Release lock 'depth' times
        for i in range(depth):
            rlock.release()
        
        # Should be able to acquire again
        rlock.acquire()
        rlock.release()


# Edge case 4: Test BoundedSemaphore with value of 0
def test_bounded_semaphore_zero_value():
    """Test BoundedSemaphore initialized with value=0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        sem = BoundedSemaphore(cache, 'zero_sem', value=0)
        
        # Should not be able to acquire when value is 0
        # This test will hang if there's a bug, so we need a timeout mechanism
        acquired = False
        
        def try_acquire():
            nonlocal acquired
            sem.acquire()
            acquired = True
        
        thread = threading.Thread(target=try_acquire)
        thread.daemon = True
        thread.start()
        thread.join(timeout=0.1)  # Wait max 100ms
        
        # The thread should still be trying to acquire (blocked)
        assert not acquired
        assert thread.is_alive()


# Edge case 5: Test Averager with alternating positive/negative values that sum to zero
@given(st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_averager_zero_sum(value):
    """Test Averager with values that sum to zero."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave = Averager(cache, 'zero_sum')
        
        # Add equal positive and negative values
        ave.add(value)
        ave.add(-value)
        
        result = ave.get()
        assert result is not None
        # The average should be very close to zero
        assert abs(result) < 1e-10


# Edge case 6: Test concurrent operations on Lock (thread safety)
def test_lock_thread_safety():
    """Test that Lock properly handles concurrent access from multiple threads."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        lock = Lock(cache, 'concurrent_lock')
        counter = 0
        iterations = 100
        
        def worker():
            nonlocal counter
            for _ in range(iterations):
                lock.acquire()
                temp = counter
                time.sleep(0.0001)  # Small delay to increase chance of race condition
                counter = temp + 1
                lock.release()
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # If lock works correctly, counter should equal total iterations
        assert counter == 5 * iterations


# Edge case 7: Test RLock owned by different thread cannot be released
def test_rlock_thread_ownership():
    """Test that RLock can only be released by the thread that acquired it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        rlock = RLock(cache, 'thread_lock')
        
        # Acquire lock in main thread
        rlock.acquire()
        
        error_occurred = False
        
        def try_release():
            nonlocal error_occurred
            try:
                rlock.release()
            except AssertionError:
                error_occurred = True
        
        # Try to release from different thread
        thread = threading.Thread(target=try_release)
        thread.start()
        thread.join()
        
        # Should have raised AssertionError
        assert error_occurred
        
        # Clean up - release from main thread
        rlock.release()


# Edge case 8: Test Averager with single value
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_averager_single_value(value):
    """Test Averager with a single value - average should equal the value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave = Averager(cache, 'single')
        
        ave.add(value)
        result = ave.get()
        
        assert result is not None
        assert math.isclose(result, value, rel_tol=1e-9)