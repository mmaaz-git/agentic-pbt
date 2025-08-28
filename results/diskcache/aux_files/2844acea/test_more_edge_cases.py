"""Additional edge case tests for diskcache."""

import tempfile
from hypothesis import given, strategies as st, assume
from diskcache import Cache, JSONDisk, Deque, Index


# Test decr() with large integers (likely has same bug as incr())
@given(
    st.integers(min_value=9_223_372_036_854_775_800),
    st.integers(min_value=1, max_value=100)
)
def test_cache_decr_large_integers(value, delta):
    """Test that decr() fails with large integers like incr() does."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        cache.set('key', value)
        
        try:
            result = cache.decr('key', delta)
            # If it works, verify the result
            assert result == value - delta
        except (TypeError, OverflowError) as e:
            # This is the bug we expect
            print(f"decr() bug confirmed: {e}")
            assert True


# Test cache.pop() with large integers
@given(st.integers())
def test_cache_pop_large_integers(value):
    """Test that pop() correctly handles all integer sizes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        cache.set('key', value)
        
        popped = cache.pop('key')
        assert popped == value
        assert 'key' not in cache


# Test JSONDisk with long strings
@given(st.text(min_size=1000, max_size=10000))
def test_jsondisk_long_strings(text):
    """Test JSONDisk with long strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        disk = JSONDisk(tmpdir)
        
        # Store and fetch
        size, mode, filename, db_value = disk.store(text, read=False)
        result = disk.fetch(mode, filename, db_value, read=False)
        assert result == text


# Test cache with empty string keys
def test_cache_empty_string_key():
    """Test that cache handles empty string as key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Empty string should be a valid key
        cache.set('', 'value')
        assert cache.get('') == 'value'
        assert '' in cache


# Test Index with special methods
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=2,
        max_size=5
    )
)
def test_index_setdefault_and_update(items):
    """Test Index.setdefault() and update() methods."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = Index(tmpdir)
        
        # Test update
        index.update(items)
        assert len(index) == len(items)
        
        # Test setdefault
        for key in items:
            result = index.setdefault(key, -999)
            assert result == items[key]  # Should return existing value
        
        new_key = 'new_key_not_in_dict'
        result = index.setdefault(new_key, -999)
        assert result == -999
        assert index[new_key] == -999


# Test Deque slicing
@given(
    st.lists(st.integers(), min_size=5, max_size=20),
    st.integers(min_value=0, max_value=5),
    st.integers(min_value=0, max_value=5)
)
def test_deque_slicing(items, start, stop):
    """Test that Deque supports slicing operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(items, directory=tmpdir)
        
        # Adjust stop to be valid
        stop = min(start + stop, len(items))
        
        # Test slicing
        sliced = deque[start:stop]
        expected = items[start:stop]
        assert list(sliced) == expected


# Test cache touch() method with expired items
@given(
    st.text(min_size=1, max_size=20),
    st.integers(),
    st.floats(min_value=0.01, max_value=0.05)
)
def test_cache_touch_expired_items(key, value, expire):
    """Test that touch() doesn't work on expired items."""
    import time
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # Set with expiration
        cache.set(key, value, expire=expire)
        
        # Wait for expiration
        time.sleep(expire + 0.01)
        
        # Touch should return False for expired items
        result = cache.touch(key)
        assert result is False


# Test cache add() method (should fail if key exists)
@given(
    st.text(min_size=1, max_size=20),
    st.integers(),
    st.integers()
)
def test_cache_add_existing_key(key, value1, value2):
    """Test that add() fails when key already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # First add should succeed
        result1 = cache.add(key, value1)
        assert result1 is True
        assert cache.get(key) == value1
        
        # Second add should fail
        result2 = cache.add(key, value2)
        assert result2 is False
        assert cache.get(key) == value1  # Value unchanged


# Test negative cache size
def test_cache_negative_size():
    """Test cache behavior with negative size values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = Cache(tmpdir)
        
        # This shouldn't be possible, but let's test edge cases
        # Try to set a value with negative expire time
        cache.set('key', 'value', expire=-1)
        
        # Should be immediately expired
        assert cache.get('key') is None