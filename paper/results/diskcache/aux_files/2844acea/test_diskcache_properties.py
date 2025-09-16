"""Property-based tests for diskcache using Hypothesis."""

import json
import math
import tempfile
import shutil
from hypothesis import assume, given, settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, Bundle

import diskcache
from diskcache import Cache, JSONDisk, Deque


# Test JSONDisk round-trip property
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
    ),
    st.integers(min_value=0, max_value=9)
)
def test_jsondisk_put_get_roundtrip(key, compress_level):
    """Test that JSONDisk.put() followed by get() preserves the key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        disk = JSONDisk(tmpdir, compress_level=compress_level)
        
        # put() returns (db_key, raw)
        db_key, raw = disk.put(key)
        
        # get() should return the original key
        result = disk.get(db_key, raw)
        
        assert result == key


@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
    ),
    st.integers(min_value=0, max_value=9)
)
def test_jsondisk_store_fetch_roundtrip(value, compress_level):
    """Test that JSONDisk.store() followed by fetch() preserves the value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        disk = JSONDisk(tmpdir, compress_level=compress_level)
        
        # store() returns (size, mode, filename, db_value)
        size, mode, filename, db_value = disk.store(value, read=False)
        
        # fetch() should return the original value
        result = disk.fetch(mode, filename, db_value, read=False)
        
        assert result == value


# Test Cache basic operations
@given(
    st.text(min_size=1),  # non-empty keys
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.binary(),
    )
)
def test_cache_set_get_consistency(key, value):
    """Test that Cache.set() followed by get() returns the same value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Set the value
        result = cache.set(key, value)
        assert result is True
        
        # Get should return the same value
        retrieved = cache.get(key)
        assert retrieved == value


@given(st.text(min_size=1))
def test_cache_delete_removes_key(key):
    """Test that after delete(), the key is no longer in the cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Set a value
        cache.set(key, "test_value")
        assert key in cache
        
        # Delete the key
        success = cache.delete(key)
        assert success is True
        
        # Key should no longer be present
        assert key not in cache
        assert cache.get(key) is None


@given(
    st.dictionaries(
        st.text(min_size=1),
        st.integers(),
        min_size=1,
        max_size=10
    )
)
def test_cache_length_consistency(items):
    """Test that cache length matches the number of unique keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Add all items
        for key, value in items.items():
            cache.set(key, value)
        
        # Length should match number of unique keys
        assert len(cache) == len(items)
        
        # All keys should be present
        for key in items:
            assert key in cache


# Test Deque properties
@given(st.lists(st.integers(), max_size=20))
def test_deque_append_pop_consistency(items):
    """Test that Deque maintains order with append and pop operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(directory=tmpdir)
        
        # Append all items
        for item in items:
            deque.append(item)
        
        # Length should match
        assert len(deque) == len(items)
        
        # Pop items and verify order (LIFO from the right)
        popped = []
        while deque:
            popped.append(deque.pop())
        
        # Should match reversed input
        assert popped == list(reversed(items))


@given(st.lists(st.integers(), min_size=1, max_size=20))
def test_deque_appendleft_popleft_consistency(items):
    """Test that Deque maintains order with appendleft and popleft operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(directory=tmpdir)
        
        # Appendleft all items
        for item in items:
            deque.appendleft(item)
        
        # Length should match
        assert len(deque) == len(items)
        
        # Popleft items and verify order (FIFO from the left)
        popped = []
        while deque:
            popped.append(deque.popleft())
        
        # Should match reversed input (since we used appendleft)
        assert popped == list(reversed(items))


@given(
    st.lists(st.integers(), max_size=10),
    st.lists(st.integers(), max_size=10)
)
def test_deque_extend_preserves_order(left_items, right_items):
    """Test that Deque.extend() preserves order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(directory=tmpdir)
        
        # Add items from the left
        for item in left_items:
            deque.appendleft(item)
        
        # Extend from the right
        deque.extend(right_items)
        
        # Convert to list to check order
        result = list(deque)
        
        # Should have left items (reversed) followed by right items
        expected = list(reversed(left_items)) + right_items
        assert result == expected


@given(st.lists(st.integers(), min_size=1, max_size=20))
def test_deque_reverse_involution(items):
    """Test that reversing a deque twice returns to original order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(items, directory=tmpdir)
        
        original = list(deque)
        
        # Reverse once
        deque.reverse()
        reversed_once = list(deque)
        
        # Reverse again
        deque.reverse()
        reversed_twice = list(deque)
        
        # Should be back to original
        assert reversed_twice == original
        assert reversed_once == list(reversed(original))


# Test Cache with JSONDisk
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.booleans(), 
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.lists(st.integers(), max_size=10),
        ),
        min_size=1,
        max_size=5
    )
)
def test_cache_with_jsondisk_roundtrip(items):
    """Test that Cache with JSONDisk preserves JSON-serializable values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir, disk=JSONDisk)
        
        # Set all items
        for key, value in items.items():
            cache.set(key, value)
        
        # Get all items and verify
        for key, expected_value in items.items():
            retrieved = cache.get(key)
            assert retrieved == expected_value


# Test increment/decrement operations
@given(
    st.text(min_size=1, max_size=20),
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-100, max_value=100)
)
def test_cache_incr_decr_consistency(key, initial, delta):
    """Test that incr and decr operations are consistent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Set initial value
        cache.set(key, initial)
        
        # Increment by delta
        new_value = cache.incr(key, delta)
        assert new_value == initial + delta
        
        # Decrement by delta (should return to original)
        final_value = cache.decr(key, delta)
        assert final_value == initial


# Test that maxlen is respected for Deque
@given(
    st.lists(st.integers(), min_size=10, max_size=30),
    st.integers(min_value=1, max_value=10)
)
def test_deque_maxlen_constraint(items, maxlen):
    """Test that Deque respects maxlen constraint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(directory=tmpdir, maxlen=maxlen)
        
        # Add all items
        for item in items:
            deque.append(item)
        
        # Length should not exceed maxlen
        assert len(deque) <= maxlen
        
        # Should contain the last maxlen items
        expected = items[-maxlen:] if len(items) > maxlen else items
        assert list(deque) == expected