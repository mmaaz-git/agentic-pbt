"""Property-based tests for diskcache library using Hypothesis."""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the diskcache path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import diskcache
from hypothesis import given, strategies as st, settings, assume
import pytest


# Strategy for valid cache keys
# Based on the code, keys can be bytes, str, int, float, or pickled objects
valid_keys = st.one_of(
    st.text(min_size=1, max_size=100),
    st.binary(min_size=1, max_size=100),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.tuples(st.text(), st.integers()),  # Compound key that will be pickled
)

# Strategy for valid cache values
valid_values = st.one_of(
    st.text(max_size=1000),
    st.binary(max_size=1000),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers(), max_size=10),  # Will be pickled
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=5),  # Will be pickled
)


@given(key=valid_keys, value=valid_values)
@settings(max_examples=100)
def test_set_get_round_trip(key, value):
    """Test that set/get is a perfect round-trip operation."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Set the value
        cache.set(key, value)
        
        # Get the value back
        retrieved = cache.get(key)
        
        # They should be equal
        assert retrieved == value
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(key=valid_keys, value=valid_values)
@settings(max_examples=100)
def test_add_only_adds_if_not_present(key, value):
    """Test that add only adds if key is not present."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # First add should succeed
        result1 = cache.add(key, value)
        assert result1 is True
        
        # Second add with same key should fail
        result2 = cache.add(key, "different_value")
        assert result2 is False
        
        # Original value should still be there
        assert cache.get(key) == value
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(key=valid_keys, value=valid_values)
@settings(max_examples=100)
def test_delete_removes_key(key, value):
    """Test that delete removes the key from cache."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Set a value
        cache.set(key, value)
        
        # Verify it's there
        assert cache.get(key) == value
        
        # Delete it
        deleted = cache.delete(key)
        assert deleted is True
        
        # Now it should return default (None)
        assert cache.get(key) is None
        
        # Deleting again should return False (nothing to delete)
        deleted2 = cache.delete(key)
        assert deleted2 is False
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(keys_values=st.lists(
    st.tuples(valid_keys, valid_values),
    min_size=1,
    max_size=10,
    unique_by=lambda x: x[0]  # Unique keys
))
@settings(max_examples=50)
def test_clear_removes_all_items(keys_values):
    """Test that clear removes all items from cache."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Add all items
        for key, value in keys_values:
            cache.set(key, value)
        
        # Verify they're all there
        for key, value in keys_values:
            assert cache.get(key) == value
        
        # Clear the cache
        cache.clear()
        
        # Now all should be gone
        for key, _ in keys_values:
            assert cache.get(key) is None
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(key=valid_keys, value1=valid_values, value2=valid_values)
@settings(max_examples=100)
def test_pop_returns_and_removes(key, value1, value2):
    """Test that pop returns the value and removes it from cache."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Set a value
        cache.set(key, value1)
        
        # Pop should return the value
        popped = cache.pop(key)
        assert popped == value1
        
        # Key should now be gone
        assert cache.get(key) is None
        
        # Pop with default should return default
        popped2 = cache.pop(key, value2)
        assert popped2 == value2
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(values=st.lists(valid_values, min_size=2, max_size=10))
@settings(max_examples=50)
def test_push_pull_fifo_order(values):
    """Test that push/pull maintains FIFO order with default settings."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Push all values with same prefix
        prefix = "test_queue"
        for value in values:
            cache.push(value, prefix=prefix, side='back')
        
        # Pull all values - should come out in same order (FIFO)
        pulled_values = []
        for _ in values:
            _, pulled_value = cache.pull(prefix=prefix, side='front')
            pulled_values.append(pulled_value)
        
        assert pulled_values == values
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(values=st.lists(valid_values, min_size=2, max_size=10))
@settings(max_examples=50)
def test_push_pull_lifo_order(values):
    """Test that push/pull maintains LIFO order when pulling from back."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Push all values with same prefix
        prefix = "test_stack"
        for value in values:
            cache.push(value, prefix=prefix, side='back')
        
        # Pull all values from back - should come out in reverse order (LIFO)
        pulled_values = []
        for _ in values:
            _, pulled_value = cache.pull(prefix=prefix, side='back')
            pulled_values.append(pulled_value)
        
        assert pulled_values == list(reversed(values))
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(key=valid_keys, value=valid_values)
@settings(max_examples=100)
def test_touch_updates_without_changing_value(key, value):
    """Test that touch updates access time without changing the value."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Set a value
        cache.set(key, value)
        
        # Touch the key
        touched = cache.touch(key)
        assert touched is True
        
        # Value should still be the same
        assert cache.get(key) == value
        
        # Touch non-existent key should return False
        fake_key = (key, "fake_suffix")  # Create a different key
        touched2 = cache.touch(fake_key)
        assert touched2 is False
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(
    data=st.lists(
        st.tuples(valid_keys, valid_values),
        min_size=1,
        max_size=20,
        unique_by=lambda x: x[0]
    )
)
@settings(max_examples=30)
def test_check_consistency(data):
    """Test that check() validates cache consistency."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Add all items
        for key, value in data:
            cache.set(key, value)
        
        # Check should pass for a valid cache (returns empty list)
        warnings_list = cache.check()
        assert warnings_list == []
        
        # All items should still be retrievable
        for key, value in data:
            assert cache.get(key) == value
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


@given(key=valid_keys, value=valid_values)
@settings(max_examples=100)
def test_contains_operator(key, value):
    """Test that __contains__ (in operator) works correctly."""
    cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(cache_dir)
        
        # Key should not be in cache initially
        assert key not in cache
        
        # Add the key
        cache.set(key, value)
        
        # Now key should be in cache
        assert key in cache
        
        # Delete the key
        cache.delete(key)
        
        # Key should not be in cache anymore
        assert key not in cache
        
        cache.close()
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Testing diskcache properties...")
    tmpdir = tempfile.mkdtemp(prefix='test-diskcache-')
    try:
        cache = diskcache.Cache(tmpdir)
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        cache.close()
        print("Basic test passed!")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)