#!/usr/bin/env /root/hypothesis-llm/envs/limits_env/bin/python3
"""Property-based tests for limits.storage module"""

import math
import time
from urllib.parse import urlparse, urlunparse

from hypothesis import assume, given, settings, strategies as st

from limits.storage import (
    MemoryStorage,
    storage_from_string,
)
from limits.storage.base import TimestampedSlidingWindow


# Test 1: incr() method always returns positive values and respects the amount
@given(
    key=st.text(min_size=1, max_size=100),
    expiry=st.floats(min_value=0.01, max_value=1000),
    amount=st.integers(min_value=1, max_value=1000),
)
def test_incr_returns_positive_and_respects_amount(key, expiry, amount):
    storage = MemoryStorage()
    result = storage.incr(key, expiry, amount)
    assert result >= amount, f"incr should return at least {amount}, got {result}"
    assert storage.get(key) == result, "get() should return the same value as incr()"


# Test 2: decr() never goes below zero (documented behavior in line 110)
@given(
    key=st.text(min_size=1, max_size=100),
    initial_value=st.integers(min_value=0, max_value=1000),
    decr_amount=st.integers(min_value=1, max_value=2000),
)
def test_decr_never_goes_below_zero(key, initial_value, decr_amount):
    storage = MemoryStorage()
    
    # Set up initial value
    if initial_value > 0:
        storage.incr(key, 100, initial_value)
    
    # Decrement
    result = storage.decr(key, decr_amount)
    
    # Verify it never goes below 0 (as per line 110: max(self.storage[key] - amount, 0))
    assert result >= 0, f"decr should never return negative, got {result}"
    assert storage.get(key) >= 0, f"storage value should never be negative"


# Test 3: Round-trip property - incr then decr by same amount
@given(
    key=st.text(min_size=1, max_size=100),
    initial=st.integers(min_value=0, max_value=1000),
    delta=st.integers(min_value=1, max_value=100),
)
def test_incr_decr_round_trip(key, initial, delta):
    storage = MemoryStorage()
    
    # Set initial value
    if initial > 0:
        storage.incr(key, 100, initial)
    
    original = storage.get(key)
    
    # Increment then decrement
    storage.incr(key, 100, delta)
    storage.decr(key, delta)
    
    final = storage.get(key)
    assert final == original, f"Round trip failed: {original} -> {final}"


# Test 4: storage_from_string factory function
@given(
    host=st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
    port=st.integers(min_value=1, max_value=65535),
)
def test_storage_from_string_memory_scheme(host, port):
    # Test memory:// scheme which should work
    uri = "memory://"
    storage = storage_from_string(uri)
    assert isinstance(storage, MemoryStorage)
    assert storage.check() is True  # Memory storage always returns True


# Test 5: acquire_entry respects limit (moving window)
@given(
    key=st.text(min_size=1, max_size=100),
    limit=st.integers(min_value=1, max_value=100),
    expiry=st.integers(min_value=1, max_value=100),
    attempts=st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=20),
)
def test_acquire_entry_respects_limit(key, limit, expiry, attempts):
    storage = MemoryStorage()
    
    acquired_count = 0
    for amount in attempts:
        if storage.acquire_entry(key, limit, expiry, amount):
            acquired_count += amount
    
    # The total acquired should never exceed the limit
    assert acquired_count <= limit, f"Acquired {acquired_count} but limit is {limit}"


# Test 6: acquire_entry fails when amount > limit
@given(
    key=st.text(min_size=1, max_size=100),
    limit=st.integers(min_value=1, max_value=100),
    expiry=st.integers(min_value=1, max_value=100),
    amount=st.integers(min_value=101, max_value=1000),
)
def test_acquire_entry_fails_when_amount_exceeds_limit(key, limit, expiry, amount):
    assume(amount > limit)
    storage = MemoryStorage()
    
    result = storage.acquire_entry(key, limit, expiry, amount)
    assert result is False, f"acquire_entry should fail when amount ({amount}) > limit ({limit})"


# Test 7: sliding window keys mathematical property
@given(
    key=st.text(min_size=1, max_size=100),
    expiry=st.integers(min_value=1, max_value=1000),
    timestamp=st.floats(min_value=1000000000, max_value=2000000000),  # Reasonable timestamps
)
def test_sliding_window_keys_consistency(key, expiry, timestamp):
    prev_key, curr_key = TimestampedSlidingWindow.sliding_window_keys(key, expiry, timestamp)
    
    # Check that keys follow the expected format
    assert prev_key.startswith(f"{key}/"), f"Previous key should start with {key}/"
    assert curr_key.startswith(f"{key}/"), f"Current key should start with {key}/"
    
    # Extract window numbers
    prev_window = int(prev_key.split("/")[-1])
    curr_window = int(curr_key.split("/")[-1])
    
    # The current window should be exactly 1 more than the previous window
    assert curr_window == prev_window + 1, f"Current window ({curr_window}) should be prev + 1 ({prev_window + 1})"


# Test 8: Sliding window weighted count calculation
@given(
    key=st.text(min_size=1, max_size=100),
    limit=st.integers(min_value=1, max_value=100),
    expiry=st.integers(min_value=1, max_value=100),
    initial_amount=st.integers(min_value=0, max_value=50),
    acquire_amount=st.integers(min_value=1, max_value=50),
)
def test_sliding_window_acquire_respects_limit(key, limit, expiry, initial_amount, acquire_amount):
    storage = MemoryStorage()
    
    # Set up initial state if needed
    if initial_amount > 0 and initial_amount <= limit:
        storage.acquire_sliding_window_entry(key, limit, expiry, initial_amount)
    
    # Try to acquire more
    if initial_amount + acquire_amount > limit:
        # Should fail if total would exceed limit
        result = storage.acquire_sliding_window_entry(key, limit, expiry, acquire_amount)
        
        # Get the sliding window info to check
        prev_count, prev_ttl, curr_count, curr_ttl = storage.get_sliding_window(key, expiry)
        weighted = prev_count * prev_ttl / expiry + curr_count
        
        # If the weighted count would exceed limit, acquire should fail
        if math.floor(weighted) + acquire_amount > limit:
            assert result is False, f"Should fail when weighted ({weighted}) + amount ({acquire_amount}) > limit ({limit})"


# Test 9: Clear removes all traces of a key
@given(
    key=st.text(min_size=1, max_size=100),
    expiry=st.floats(min_value=0.01, max_value=100),
    amount=st.integers(min_value=1, max_value=100),
)
def test_clear_removes_key_completely(key, expiry, amount):
    storage = MemoryStorage()
    
    # Add some data
    storage.incr(key, expiry, amount)
    assert storage.get(key) > 0
    
    # Clear it
    storage.clear(key)
    
    # Verify it's gone
    assert storage.get(key) == 0, "After clear, get() should return 0"
    assert key not in storage.storage, "Key should be removed from storage"
    assert key not in storage.expirations, "Key should be removed from expirations"
    assert key not in storage.events, "Key should be removed from events"


# Test 10: Reset clears everything and returns count
@given(
    keys=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10, unique=True),
    amounts=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10),
)
def test_reset_clears_all_storage(keys, amounts):
    assume(len(keys) == len(amounts))
    storage = MemoryStorage()
    
    # Add data for multiple keys
    for key, amount in zip(keys, amounts):
        storage.incr(key, 100, amount)
    
    # Reset
    num_items = storage.reset()
    
    # Verify everything is cleared
    assert len(storage.storage) == 0, "Storage should be empty after reset"
    assert len(storage.expirations) == 0, "Expirations should be empty after reset"
    assert len(storage.events) == 0, "Events should be empty after reset"
    assert num_items >= 0, "Reset should return non-negative count"
    
    # All keys should return 0
    for key in keys:
        assert storage.get(key) == 0, f"Key {key} should return 0 after reset"


if __name__ == "__main__":
    print("Running property-based tests for limits.storage...")
    import pytest
    pytest.main([__file__, "-v"])