"""Property-based tests for diskcache.FanoutCache using Hypothesis."""

import tempfile
import shutil
import math
from hypothesis import given, strategies as st, settings, assume
from diskcache import FanoutCache


# Helper strategies
simple_keys = st.one_of(
    st.text(min_size=1, max_size=100),  # strings
    st.integers(),  # integers
    st.floats(allow_nan=False, allow_infinity=False),  # floats
    st.binary(min_size=1, max_size=100),  # bytes
)

simple_values = st.one_of(
    st.text(max_size=1000),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.binary(max_size=1000),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=5),
)


def create_cache(shards=4):
    """Create a temporary FanoutCache for testing."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    return FanoutCache(directory=temp_dir, shards=shards)


@given(simple_keys, simple_values, st.integers(min_value=2, max_value=16))
def test_sharding_consistency(key, value, shards):
    """Test that the same key always maps to the same shard."""
    cache = create_cache(shards=shards)
    try:
        # Set the value
        cache[key] = value
        
        # Calculate which shard this key should be in
        expected_shard = cache._hash(key) % cache._count
        
        # Verify the key is in the expected shard
        assert key in cache._shards[expected_shard]
        
        # Verify the key is NOT in other shards
        for i, shard in enumerate(cache._shards):
            if i != expected_shard:
                assert key not in shard
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(simple_keys, simple_values)
def test_set_get_round_trip(key, value):
    """Test that values can be set and retrieved correctly."""
    cache = create_cache()
    try:
        # Set the value
        cache[key] = value
        
        # Get it back
        retrieved = cache[key]
        
        # Should be equal
        if isinstance(value, float) and math.isnan(value):
            assert math.isnan(retrieved)
        else:
            assert retrieved == value
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(simple_keys, st.integers(min_value=-1000, max_value=1000), 
       st.integers(min_value=1, max_value=100))
def test_incr_decr_inverse(key, initial, delta):
    """Test that increment and decrement are inverse operations."""
    cache = create_cache()
    try:
        # Set initial value
        cache[key] = initial
        
        # Increment by delta
        new_val = cache.incr(key, delta=delta)
        assert new_val == initial + delta
        
        # Decrement by delta
        final_val = cache.decr(key, delta=delta)
        assert final_val == initial
        
        # Verify the value is back to initial
        assert cache[key] == initial
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(st.lists(st.tuples(simple_keys, simple_values), min_size=1, max_size=20))
def test_stats_consistency(items):
    """Test that stats are correctly summed across shards."""
    cache = create_cache()
    try:
        # Enable stats
        cache.stats(enable=True, reset=True)
        
        # Add items
        for key, value in items:
            cache[key] = value
        
        # Get some items (to generate hits)
        for key, _ in items[:len(items)//2]:
            _ = cache.get(key)
        
        # Get some non-existent items (to generate misses)
        _ = cache.get("nonexistent_key_1")
        _ = cache.get("nonexistent_key_2")
        
        # Get total stats
        total_hits, total_misses = cache.stats()
        
        # Get individual shard stats and sum them
        shard_hits = 0
        shard_misses = 0
        for shard in cache._shards:
            hits, misses = shard.stats()
            shard_hits += hits
            shard_misses += misses
        
        # They should be equal
        assert total_hits == shard_hits
        assert total_misses == shard_misses
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(simple_keys, simple_values)
def test_contains_get_consistency(key, value):
    """Test that if a key is in the cache, getting it should not raise KeyError."""
    cache = create_cache()
    try:
        # Add the item
        cache[key] = value
        
        # If it's in the cache
        if key in cache:
            # Getting it should not raise KeyError
            result = cache[key]
            assert result == value
        
        # Delete the item
        del cache[key]
        
        # Now it should not be in cache
        assert key not in cache
        
        # And getting it should raise KeyError
        try:
            _ = cache[key]
            assert False, "Should have raised KeyError"
        except KeyError:
            pass  # Expected
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(simple_keys, simple_values, st.integers())
def test_add_idempotence(key, value1, value2):
    """Test that add only succeeds once for the same key."""
    assume(value1 != value2)  # Make sure values are different
    
    cache = create_cache()
    try:
        # First add should succeed
        result1 = cache.add(key, value1)
        assert result1 is True
        
        # Second add should fail
        result2 = cache.add(key, value2)
        assert result2 is False
        
        # Value should still be the first one
        assert cache[key] == value1
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(st.lists(st.tuples(simple_keys, simple_values), min_size=1, max_size=10))
def test_length_consistency(items):
    """Test that total length equals sum of shard lengths."""
    cache = create_cache()
    try:
        # Add items
        for key, value in items:
            cache[key] = value
        
        # Get total length
        total_len = len(cache)
        
        # Sum individual shard lengths
        shard_sum = sum(len(shard) for shard in cache._shards)
        
        # They should be equal
        assert total_len == shard_sum
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(st.lists(simple_keys, min_size=1, max_size=10, unique=True))
def test_iteration_consistency(keys):
    """Test that iteration yields all keys exactly once."""
    cache = create_cache()
    try:
        # Add all keys with dummy values
        for key in keys:
            cache[key] = "value"
        
        # Collect all keys from iteration
        iterated_keys = list(cache)
        
        # Should have the same keys (order may differ)
        assert set(iterated_keys) == set(keys)
        assert len(iterated_keys) == len(keys)
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(simple_keys, simple_values)
def test_pop_consistency(key, value):
    """Test that pop removes the key and returns the value."""
    cache = create_cache()
    try:
        # Add the item
        cache[key] = value
        
        # Pop it
        popped = cache.pop(key)
        assert popped == value
        
        # Key should no longer be in cache
        assert key not in cache
        
        # Popping again should return default
        default = "my_default"
        popped2 = cache.pop(key, default=default)
        assert popped2 == default
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


@given(st.lists(st.tuples(simple_keys, simple_values), min_size=2, max_size=10))
def test_clear_removes_all(items):
    """Test that clear removes all items from cache."""
    cache = create_cache()
    try:
        # Add items
        for key, value in items:
            cache[key] = value
        
        # Verify they're there
        assert len(cache) == len(items)
        
        # Clear the cache
        count = cache.clear()
        
        # Should have removed all items
        assert count == len(items)
        assert len(cache) == 0
        
        # None of the keys should be in cache
        for key, _ in items:
            assert key not in cache
    finally:
        cache.close()
        shutil.rmtree(cache.directory, ignore_errors=True)


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Testing FanoutCache properties...")
    test_set_get_round_trip()
    print("Basic test passed!")