import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import time
import math
import threading
from hypothesis import given, strategies as st, assume, settings, seed
from limits.storage import storage_from_string, MemoryStorage
from limits.storage.base import TimestampedSlidingWindow
from limits.errors import ConfigurationError
import pytest

# Test edge cases with zero and negative expiry
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=-100, max_value=0),
    st.integers(min_value=1, max_value=100)
)
def test_zero_or_negative_expiry(key, expiry, amount):
    """Test behavior with zero or negative expiry values"""
    storage = MemoryStorage()
    
    if expiry <= 0:
        # This might cause issues with division by zero or negative values
        try:
            result = storage.incr(key, expiry=expiry, amount=amount)
            # If it doesn't raise, check the value is sensible
            assert result >= 0
            
            # Try to get the value - it might have expired immediately
            value = storage.get(key)
            assert value >= 0
        except (ValueError, ZeroDivisionError):
            # This is acceptable behavior
            pass

# Test extreme amounts 
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=2**31, max_value=2**63-1),
    st.integers(min_value=60, max_value=3600)
)
def test_extreme_amounts(key, amount, expiry):
    """Test with very large amounts that might cause overflow"""
    storage = MemoryStorage()
    
    # Try incrementing with huge amounts
    result = storage.incr(key, expiry=expiry, amount=amount)
    assert result == amount
    
    # Try incrementing again - might overflow
    result2 = storage.incr(key, expiry=expiry, amount=amount)
    # Should be 2*amount or handle overflow gracefully
    assert result2 >= amount  # At minimum should be >= amount

# Test sliding window with zero expiry
@given(
    st.text(min_size=1, max_size=100),
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_sliding_window_keys_zero_expiry(key, timestamp):
    """Test sliding window key generation with zero expiry"""
    # Zero expiry would cause division by zero
    try:
        prev_key, curr_key = TimestampedSlidingWindow.sliding_window_keys(key, 0, timestamp)
        # If it doesn't raise, it's a bug
        assert False, "Expected ZeroDivisionError but got keys"
    except ZeroDivisionError:
        # Expected behavior
        pass

# Test get_expiry edge cases
@given(st.text(min_size=1, max_size=100))
def test_get_expiry_nonexistent_key(key):
    """Test get_expiry on non-existent keys"""
    storage = MemoryStorage()
    
    # Getting expiry for non-existent key
    expiry = storage.get_expiry(key)
    # According to line 165, should return time.time() for non-existent keys
    current_time = time.time()
    # Should be very close to current time
    assert abs(expiry - current_time) < 1.0

# Test concurrent operations that might cause race conditions
@given(
    st.text(min_size=1, max_size=50),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=60, max_value=120)
)
@settings(max_examples=20, deadline=5000)
def test_concurrent_incr_decr(key, amount, expiry):
    """Test concurrent increment and decrement operations"""
    storage = MemoryStorage()
    storage.incr(key, expiry=expiry, amount=100)  # Start with 100
    
    results = []
    def increment():
        for _ in range(10):
            storage.incr(key, expiry=expiry, amount=amount)
    
    def decrement():
        for _ in range(10):
            storage.decr(key, amount=amount)
    
    # Run concurrent operations
    t1 = threading.Thread(target=increment)
    t2 = threading.Thread(target=decrement)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Final value should be 100 (initial) + 0 (net change)
    final = storage.get(key)
    assert final == 100
    assert final >= 0  # Should never be negative

# Test acquiring more entries than limit in sliding window
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=60, max_value=3600)
)
def test_sliding_window_overacquire(key, limit, expiry):
    """Test that sliding window correctly rejects over-limit acquisitions"""
    storage = MemoryStorage()
    
    # Try to acquire more than limit in one go
    result = storage.acquire_sliding_window_entry(key, limit, expiry, amount=limit+1)
    assert result is False  # Should always fail
    
    # Verify nothing was acquired
    prev, prev_ttl, curr, curr_ttl = storage.get_sliding_window(key, expiry)
    assert prev == 0
    assert curr == 0

# Test empty string keys
@given(st.integers(min_value=1, max_value=100))
def test_empty_string_key(amount):
    """Test operations with empty string as key"""
    storage = MemoryStorage()
    
    # Empty string should be valid key
    result = storage.incr("", expiry=60, amount=amount)
    assert result == amount
    
    value = storage.get("")
    assert value == amount
    
    storage.clear("")
    assert storage.get("") == 0

# Test float expiry values (should they be allowed?)
@given(
    st.text(min_size=1, max_size=100),
    st.floats(min_value=0.001, max_value=3600.0, allow_nan=False, allow_infinity=False),
    st.integers(min_value=1, max_value=100)
)
def test_float_expiry_values(key, expiry, amount):
    """Test with float expiry values"""
    storage = MemoryStorage()
    
    # Float expiry might cause issues
    result = storage.incr(key, expiry=expiry, amount=amount)
    assert result == amount
    
    # Check it's stored correctly
    value = storage.get(key)
    assert value == amount

# Test the weighted count calculation edge case
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=60, max_value=3600)
)
def test_sliding_window_weighted_count_edge(key, expiry):
    """Test edge case in weighted count calculation"""
    storage = MemoryStorage()
    
    # Set up specific scenario where weighted count might have precision issues
    # First fill up to limit
    limit = 10
    for i in range(limit):
        result = storage.acquire_sliding_window_entry(key, limit, expiry, 1)
        if not result:
            break
    
    # Get the weighted count
    prev, prev_ttl, curr, curr_ttl = storage.get_sliding_window(key, expiry)
    
    # Calculate weighted count as the code does
    weighted = prev * prev_ttl / expiry + curr
    
    # Floor of weighted should not exceed limit
    assert math.floor(weighted) <= limit
    
    # Try one more acquisition - should fail
    result = storage.acquire_sliding_window_entry(key, limit, expiry, 1)
    # Might succeed if time has passed and weight decreased
    if not result:
        # If it failed, weighted count should be at limit
        prev2, prev_ttl2, curr2, curr_ttl2 = storage.get_sliding_window(key, expiry)
        weighted2 = prev2 * prev_ttl2 / expiry + curr2
        assert math.floor(weighted2) >= limit or curr2 >= limit

# Test the clear_sliding_window method
@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=60, max_value=3600)
)
def test_clear_sliding_window(key, expiry):
    """Test that clear_sliding_window properly clears both windows"""
    storage = MemoryStorage()
    
    # Acquire some entries
    storage.acquire_sliding_window_entry(key, 10, expiry, 5)
    
    # Verify entries exist
    prev, _, curr, _ = storage.get_sliding_window(key, expiry)
    total_before = prev + curr
    assert total_before >= 0  # Might be 0 or 5 depending on timing
    
    # Clear the sliding window
    storage.clear_sliding_window(key, expiry)
    
    # Both windows should be cleared
    prev, _, curr, _ = storage.get_sliding_window(key, expiry)
    assert prev == 0
    assert curr == 0