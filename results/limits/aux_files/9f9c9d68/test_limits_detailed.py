import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import time
import math
import threading
from hypothesis import given, strategies as st, assume, settings, seed, note
from limits.storage import storage_from_string, MemoryStorage
from limits.storage.base import TimestampedSlidingWindow
from limits.errors import ConfigurationError
import pytest

# Test the bisect operations in get_moving_window  
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=60)
)
def test_moving_window_bisect_edge_case(key, limit, expiry):
    """Test edge cases in bisect operations in get_moving_window"""
    storage = MemoryStorage()
    
    # The bisect operation uses negative keys which is unusual
    # Try to trigger edge cases with rapid acquisitions
    for i in range(min(limit, 10)):
        storage.acquire_entry(key, limit, expiry, 1)
    
    # Get the window - this uses bisect internally
    start, count = storage.get_moving_window(key, limit, expiry)
    
    # Count should match what we acquired (within expiry window)
    assert count >= 0
    assert count <= min(limit, 10)
    
    # Start time should be reasonable
    current = time.time()
    assert start <= current
    assert start >= current - expiry - 1  # Allow 1 second tolerance

# Test the timer cleanup mechanism
@given(st.text(min_size=1, max_size=100))
def test_timer_cleanup_mechanism(key):
    """Test that the timer cleanup mechanism works"""
    storage = MemoryStorage()
    
    # Add a key with very short expiry
    storage.incr(key, expiry=0.01, amount=10)
    
    # Value should exist initially
    assert storage.get(key) == 10
    
    # Wait for expiry
    time.sleep(0.02)
    
    # Trigger expiry check
    storage._MemoryStorage__expire_events()
    
    # Value should be expired
    assert storage.get(key) == 0

# Test the storage registry and scheme registration
def test_storage_scheme_registration():
    """Test that storage schemes are properly registered"""
    from limits.storage.registry import SCHEMES
    
    # Memory should be registered
    assert "memory" in SCHEMES
    assert SCHEMES["memory"] == MemoryStorage
    
    # Creating via string should work
    storage = storage_from_string("memory://")
    assert isinstance(storage, MemoryStorage)

# Test URL parsing edge cases
@given(st.text(min_size=1, max_size=200))
def test_storage_from_string_url_parsing(text):
    """Test URL parsing in storage_from_string"""
    # Try various malformed URLs
    if "://" not in text:
        # Not a valid URL format
        with pytest.raises(ConfigurationError):
            storage_from_string(text)
    else:
        # Extract scheme
        scheme = text.split("://")[0]
        if scheme not in ["memory", "memcached", "redis", "redis+cluster", "redis+sentinel", "mongodb", 
                          "async+memory", "async+memcached", "async+redis", "async+redis+cluster", 
                          "async+redis+sentinel", "async+mongodb"]:
            with pytest.raises(ConfigurationError, match="unknown storage scheme"):
                storage_from_string(text)

# Test the race condition mentioned in the code comment
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=5, max_value=20),
    st.integers(min_value=60, max_value=120)
)
@settings(max_examples=10, deadline=10000)
def test_sliding_window_race_condition(key, limit, expiry):
    """Test the race condition mentioned in line 211-213 of memory.py"""
    storage = MemoryStorage()
    
    # Fill up to just below limit
    for _ in range(limit - 1):
        storage.acquire_sliding_window_entry(key, limit, expiry, 1)
    
    # Now try concurrent acquisitions for the last spot
    success_count = [0]
    failure_count = [0]
    
    def try_acquire():
        if storage.acquire_sliding_window_entry(key, limit, expiry, 1):
            success_count[0] += 1
        else:
            failure_count[0] += 1
    
    # Launch multiple threads trying to get the last spot
    threads = []
    for _ in range(10):
        t = threading.Thread(target=try_acquire)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # At most 1 should succeed (the last available spot)
    assert success_count[0] <= 1
    
    # Check final state
    prev, prev_ttl, curr, _ = storage.get_sliding_window(key, expiry)
    weighted = prev * prev_ttl / expiry + curr
    # Due to the race condition and reversion, might be slightly under limit
    assert math.floor(weighted) <= limit

# Test incr with existing key and new expiry
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=60, max_value=120),
    st.integers(min_value=180, max_value=360)
)
def test_incr_existing_key_new_expiry(key, amount1, expiry1, expiry2):
    """Test incrementing existing key doesn't reset expiry"""
    storage = MemoryStorage()
    
    # First increment sets expiry
    storage.incr(key, expiry=expiry1, amount=amount1)
    first_expiry = storage.get_expiry(key)
    
    # Wait a tiny bit
    time.sleep(0.01)
    
    # Second increment with different expiry shouldn't change it
    storage.incr(key, expiry=expiry2, amount=1)
    second_expiry = storage.get_expiry(key)
    
    # Expiry should not have changed (line 96-97 in memory.py)
    # Allow small tolerance for timing
    assert abs(first_expiry - second_expiry) < 0.1

# Test acquire_entry with amount = 0
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=60, max_value=120)
)
def test_acquire_entry_zero_amount(key, limit, expiry):
    """Test acquire_entry with amount=0"""
    storage = MemoryStorage()
    
    # Acquiring 0 entries should succeed (it's within any limit)
    result = storage.acquire_entry(key, limit, expiry, amount=0)
    assert result is True
    
    # But shouldn't actually add any entries
    _, count = storage.get_moving_window(key, limit, expiry)
    assert count == 0

# Test the oldest entry calculation in line 151-152
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=2, max_value=10),
    st.floats(min_value=0.01, max_value=0.1)  # Use very short expiry to avoid timeout
)
@settings(deadline=5000)  # Increase deadline for this test
def test_acquire_entry_oldest_calculation(key, limit, expiry):
    """Test the oldest entry calculation when checking limits"""
    storage = MemoryStorage()
    
    # Fill to limit
    for i in range(limit):
        result = storage.acquire_entry(key, limit, expiry, 1)
        assert result is True
    
    # Next one should fail
    result = storage.acquire_entry(key, limit, expiry, 1)
    assert result is False
    
    # Wait for first entry to expire
    time.sleep(expiry + 0.02)
    
    # Now should succeed again
    result = storage.acquire_entry(key, limit, expiry, 1)
    assert result is True

# Test division by zero protection in sliding window TTL calculation
@given(st.text(min_size=1, max_size=100))
def test_sliding_window_ttl_zero_expiry(key):
    """Test TTL calculation with zero expiry"""
    storage = MemoryStorage()
    
    # This should handle zero expiry gracefully or raise
    try:
        # Zero expiry in sliding window
        prev, prev_ttl, curr, curr_ttl = storage.get_sliding_window(key, 0)
        # If it doesn't raise, TTLs should be sensible
        assert prev_ttl >= 0
        assert curr_ttl >= 0
    except ZeroDivisionError:
        # This is acceptable
        pass

# Test __getstate__ and __setstate__ for pickling
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=100)
)
def test_storage_pickling(key, amount):
    """Test that storage can be pickled and unpickled"""
    import pickle
    
    storage = MemoryStorage()
    storage.incr(key, expiry=60, amount=amount)
    
    # Pickle and unpickle
    pickled = pickle.dumps(storage)
    restored = pickle.loads(pickled)
    
    # Should preserve state
    assert restored.get(key) == amount
    
    # Should be able to continue operations
    restored.incr(key, expiry=60, amount=1)
    assert restored.get(key) == amount + 1