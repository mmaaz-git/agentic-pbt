import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import time
import math
from hypothesis import given, strategies as st, assume, settings
from limits.storage import storage_from_string, MemoryStorage
from limits.storage.base import TimestampedSlidingWindow
from limits.errors import ConfigurationError
import pytest

# Test 1: storage_from_string should correctly parse URIs
@given(st.text(min_size=1, max_size=50).filter(lambda x: "/" not in x and ":" not in x))
def test_storage_from_string_unknown_scheme(scheme):
    """Test that unknown schemes raise ConfigurationError as documented"""
    with pytest.raises(ConfigurationError, match="unknown storage scheme"):
        storage_from_string(f"{scheme}://localhost")

@given(st.integers(min_value=1, max_value=65535))
def test_storage_from_string_memory_scheme(port):
    """Test that memory:// scheme creates MemoryStorage instances"""
    storage = storage_from_string(f"memory://localhost:{port}")
    assert isinstance(storage, MemoryStorage)
    assert storage.check() is True  # Memory storage should always be healthy

# Test 2: Counter non-negativity invariant
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=1000)
)
def test_counter_never_negative(key, initial_amount, decr_amount):
    """The decr method ensures counters never go negative (line 110 in memory.py)"""
    storage = MemoryStorage()
    
    # Set up initial value
    storage.incr(key, expiry=60, amount=initial_amount)
    result = storage.get(key)
    assert result == initial_amount
    
    # Decrement by more than current value
    final_value = storage.decr(key, amount=decr_amount)
    
    # Counter should never be negative
    assert final_value >= 0
    assert storage.get(key) >= 0
    
    # If we decremented by more than we had, should be 0
    if decr_amount >= initial_amount:
        assert final_value == 0
        assert storage.get(key) == 0

# Test 3: incr/decr inverse operations 
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=60, max_value=3600)
)
def test_incr_decr_inverse(key, amount, expiry):
    """incr and decr should be inverse operations when within bounds"""
    storage = MemoryStorage()
    
    # Start from 0
    initial = storage.get(key)
    assert initial == 0
    
    # Increment
    after_incr = storage.incr(key, expiry=expiry, amount=amount)
    assert after_incr == amount
    
    # Decrement by same amount
    after_decr = storage.decr(key, amount=amount)
    assert after_decr == 0
    assert storage.get(key) == initial

# Test 4: Sliding window key generation property
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=3600),
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_sliding_window_keys_consistency(key, expiry, timestamp):
    """Sliding window keys should follow predictable pattern"""
    prev_key, curr_key = TimestampedSlidingWindow.sliding_window_keys(key, expiry, timestamp)
    
    # Keys should start with the original key
    assert prev_key.startswith(f"{key}/")
    assert curr_key.startswith(f"{key}/")
    
    # Extract window indices
    prev_idx = int(prev_key.split("/")[-1])
    curr_idx = int(curr_key.split("/")[-1])
    
    # Current window should be after or equal to previous window
    assert curr_idx >= prev_idx
    
    # The difference should be at most 1 (adjacent windows)
    assert curr_idx - prev_idx <= 1
    
    # Verify the calculation matches the documented formula
    expected_prev = int((timestamp - expiry) / expiry)
    expected_curr = int(timestamp / expiry)
    assert prev_idx == expected_prev
    assert curr_idx == expected_curr

# Test 5: acquire_entry limit enforcement
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=60, max_value=3600),
    st.integers(min_value=1, max_value=200)
)
def test_acquire_entry_limit_enforcement(key, limit, expiry, amount):
    """acquire_entry should reject amounts exceeding the limit"""
    storage = MemoryStorage()
    
    # If amount > limit, should always fail (line 142-143 in memory.py)
    if amount > limit:
        result = storage.acquire_entry(key, limit, expiry, amount)
        assert result is False
    else:
        # First acquisition within limit should succeed
        result = storage.acquire_entry(key, limit, expiry, amount)
        assert result is True
        
        # Acquiring again with remaining capacity
        remaining = limit - amount
        if remaining > 0:
            # Should succeed if we request within remaining
            result2 = storage.acquire_entry(key, limit, expiry, 1)
            # This might fail if the window is full
            assert isinstance(result2, bool)

# Test 6: Moving window entry tracking
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=60)
)
@settings(max_examples=100)
def test_moving_window_count_consistency(key, limit, expiry):
    """Moving window should correctly track the number of entries"""
    storage = MemoryStorage()
    
    # Initially should have 0 entries
    _, count = storage.get_moving_window(key, limit, expiry)
    assert count == 0
    
    # Acquire some entries
    acquired = 0
    for i in range(limit):
        if storage.acquire_entry(key, limit, expiry, 1):
            acquired += 1
    
    # Check the count matches what we acquired
    _, count = storage.get_moving_window(key, limit, expiry)
    assert count == acquired
    assert count <= limit  # Should never exceed limit

# Test 7: clear operation completeness
@given(st.text(min_size=1, max_size=100))
def test_clear_removes_all_data(key):
    """clear should remove all data associated with a key"""
    storage = MemoryStorage()
    
    # Set up some data
    storage.incr(key, expiry=60, amount=10)
    storage.acquire_entry(key, limit=5, expiry=60, amount=2)
    
    # Verify data exists
    assert storage.get(key) == 10
    _, count = storage.get_moving_window(key, 5, 60)
    assert count > 0
    
    # Clear the key
    storage.clear(key)
    
    # All data should be gone
    assert storage.get(key) == 0
    _, count = storage.get_moving_window(key, 5, 60)
    assert count == 0

# Test 8: reset operation
@given(
    st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    st.integers(min_value=1, max_value=100)
)
def test_reset_clears_all_storage(keys, amount):
    """reset should clear all storage and return the count"""
    storage = MemoryStorage()
    
    # Add data for multiple keys
    for key in keys:
        storage.incr(key, expiry=60, amount=amount)
    
    # Reset storage
    count = storage.reset()
    assert count is not None
    assert count >= 0
    
    # All keys should be cleared
    for key in keys:
        assert storage.get(key) == 0

# Test 9: Sliding window weighted count calculation
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=5, max_value=100),
    st.integers(min_value=60, max_value=3600)
)
@settings(max_examples=50)
def test_sliding_window_weighted_count(key, limit, expiry):
    """Sliding window weighted count should respect the limit"""
    storage = MemoryStorage()
    
    # Try to acquire entries up to the limit
    acquired = 0
    for _ in range(limit + 10):  # Try more than limit
        if storage.acquire_sliding_window_entry(key, limit, expiry, 1):
            acquired += 1
    
    # Should not exceed limit
    assert acquired <= limit
    
    # Get window info
    prev_count, prev_ttl, curr_count, curr_ttl = storage.get_sliding_window(key, expiry)
    
    # Counts should be non-negative
    assert prev_count >= 0
    assert curr_count >= 0
    
    # TTLs should be non-negative
    assert prev_ttl >= 0
    assert curr_ttl >= 0
    
    # Weighted count should not exceed limit (with floor)
    weighted = prev_count * prev_ttl / expiry + curr_count
    assert math.floor(weighted) <= limit