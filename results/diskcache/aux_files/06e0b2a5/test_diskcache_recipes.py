import math
import os
import tempfile
import threading
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import diskcache from the virtual environment
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')
import diskcache
from diskcache.recipes import Averager, RLock, BoundedSemaphore, Lock


# Property 1: Averager should maintain correct mathematical average
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10), min_size=1))
def test_averager_mathematical_average(values):
    """Test that Averager.get() returns the correct mathematical average of added values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave = Averager(cache, 'test_key')
        
        for value in values:
            ave.add(value)
        
        result = ave.get()
        expected = sum(values) / len(values)
        
        assert result is not None
        assert math.isclose(result, expected, rel_tol=1e-9)


# Property 2: Averager should return None when no values added
@given(st.text(min_size=1))
def test_averager_empty_returns_none(key):
    """Test that Averager.get() and pop() return None when no values have been added."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave = Averager(cache, key)
        
        assert ave.get() is None
        assert ave.pop() is None


# Property 3: Averager pop should return average and clear the key
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10), min_size=1))
def test_averager_pop_clears_and_returns_average(values):
    """Test that Averager.pop() returns the average and clears the key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave = Averager(cache, 'test_key')
        
        for value in values:
            ave.add(value)
        
        expected = sum(values) / len(values)
        result = ave.pop()
        
        assert result is not None
        assert math.isclose(result, expected, rel_tol=1e-9)
        
        # After pop, get should return None
        assert ave.get() is None


# Property 4: RLock can be acquired multiple times by same thread
@given(st.integers(min_value=1, max_value=10))
def test_rlock_reentrant_acquisition(acquire_count):
    """Test that RLock can be acquired multiple times by the same thread."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        rlock = RLock(cache, 'test_lock')
        
        # Acquire the lock multiple times
        for _ in range(acquire_count):
            rlock.acquire()
        
        # Release the lock the same number of times
        for _ in range(acquire_count):
            rlock.release()
        
        # After all releases, we should be able to acquire again
        rlock.acquire()
        rlock.release()


# Property 5: RLock release without acquire raises AssertionError
@given(st.text(min_size=1))
def test_rlock_release_unacquired_raises_assertion(key):
    """Test that RLock.release() raises AssertionError when lock is not acquired."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        rlock = RLock(cache, key)
        
        with pytest.raises(AssertionError, match="cannot release un-acquired lock"):
            rlock.release()


# Property 6: RLock release more than acquired raises AssertionError
@given(st.integers(min_value=1, max_value=5))
def test_rlock_over_release_raises_assertion(acquire_count):
    """Test that releasing RLock more times than acquired raises AssertionError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        rlock = RLock(cache, 'test_lock')
        
        # Acquire the lock
        for _ in range(acquire_count):
            rlock.acquire()
        
        # Release correctly
        for _ in range(acquire_count):
            rlock.release()
        
        # One more release should fail
        with pytest.raises(AssertionError, match="cannot release un-acquired lock"):
            rlock.release()


# Property 7: BoundedSemaphore respects maximum value
@given(
    st.integers(min_value=1, max_value=10),  # initial value
    st.lists(st.sampled_from(['acquire', 'release']), min_size=1, max_size=20)
)
def test_bounded_semaphore_respects_bounds(initial_value, operations):
    """Test that BoundedSemaphore never exceeds its initial value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        sem = BoundedSemaphore(cache, 'test_sem', value=initial_value)
        
        acquired_count = 0
        
        for op in operations:
            if op == 'acquire':
                if acquired_count < initial_value:
                    sem.acquire()
                    acquired_count += 1
            else:  # release
                if acquired_count > 0:
                    sem.release()
                    acquired_count -= 1
                else:
                    # Should raise AssertionError
                    with pytest.raises(AssertionError, match="cannot release un-acquired semaphore"):
                        sem.release()


# Property 8: BoundedSemaphore release without acquire raises AssertionError
@given(st.integers(min_value=1, max_value=10))
def test_bounded_semaphore_release_unacquired_raises(initial_value):
    """Test that BoundedSemaphore.release() raises AssertionError when not acquired."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        sem = BoundedSemaphore(cache, 'test_sem', value=initial_value)
        
        with pytest.raises(AssertionError, match="cannot release un-acquired semaphore"):
            sem.release()


# Property 9: Lock is exclusive (cannot be acquired twice without release)
@given(st.text(min_size=1))
def test_lock_is_exclusive(key):
    """Test that Lock can only be acquired once at a time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        lock = Lock(cache, key)
        
        # First acquire should succeed
        lock.acquire()
        
        # Check that lock is held
        assert lock.locked()
        
        # Release the lock
        lock.release()
        
        # After release, locked should return False
        assert not lock.locked()
        
        # Should be able to acquire again
        lock.acquire()
        lock.release()


# Property 10: Multiple Averagers with different keys are independent
@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10), min_size=1),
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10), min_size=1),
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_averager_independence(values1, values2, key1, key2):
    """Test that Averagers with different keys maintain independent averages."""
    assume(key1 != key2)  # Ensure keys are different
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        ave1 = Averager(cache, key1)
        ave2 = Averager(cache, key2)
        
        for value in values1:
            ave1.add(value)
        
        for value in values2:
            ave2.add(value)
        
        result1 = ave1.get()
        result2 = ave2.get()
        expected1 = sum(values1) / len(values1)
        expected2 = sum(values2) / len(values2)
        
        assert math.isclose(result1, expected1, rel_tol=1e-9)
        assert math.isclose(result2, expected2, rel_tol=1e-9)