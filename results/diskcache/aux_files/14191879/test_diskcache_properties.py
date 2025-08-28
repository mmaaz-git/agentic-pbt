#!/usr/bin/env python3

import sys
import tempfile
import shutil
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import diskcache
from diskcache.core import Disk, JSONDisk, Cache
from hypothesis import given, strategies as st, settings, assume
import math

# Test 1: Disk serialization round-trip
@given(
    key=st.one_of(
        st.integers(min_value=-9223372036854775808, max_value=9223372036854775807),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(min_size=1),
        st.binary(min_size=1)
    )
)
def test_disk_put_get_round_trip(key):
    """Test that Disk.get(Disk.put(key)) returns the original key for basic types."""
    tmpdir = tempfile.mkdtemp()
    try:
        disk = Disk(tmpdir)
        db_key, raw = disk.put(key)
        retrieved = disk.get(db_key, raw)
        
        # Handle bytes separately since sqlite3.Binary wraps them
        if isinstance(key, bytes):
            assert retrieved == key
        else:
            assert retrieved == key
    finally:
        shutil.rmtree(tmpdir)


# Test 2: Cache set/get consistency
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.binary()
    )
)
@settings(max_examples=200)
def test_cache_set_get_consistency(key, value):
    """Test that after cache.set(key, value), cache.get(key) returns that value."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        cache.set(key, value)
        retrieved = cache.get(key)
        
        if isinstance(value, float) and math.isnan(value):
            assert math.isnan(retrieved)
        else:
            assert retrieved == value
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test 3: Add operation uniqueness
@given(
    key=st.text(min_size=1, max_size=100),
    value1=st.integers(),
    value2=st.integers()
)
@settings(max_examples=200)
def test_cache_add_uniqueness(key, value1, value2):
    """Test that add() only succeeds if key is not present."""
    assume(value1 != value2)  # Make sure values are different
    
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # First add should succeed
        result1 = cache.add(key, value1)
        assert result1 is True
        assert cache.get(key) == value1
        
        # Second add should fail (key already exists)
        result2 = cache.add(key, value2)
        assert result2 is False
        assert cache.get(key) == value1  # Value should not change
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test 4: Increment/decrement inverse operations
@given(
    key=st.text(min_size=1, max_size=100),
    initial=st.integers(min_value=-1000000, max_value=1000000),
    delta=st.integers(min_value=-10000, max_value=10000)
)
@settings(max_examples=200)
def test_increment_decrement_inverse(key, initial, delta):
    """Test that incr and decr are inverse operations."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Set initial value
        cache.set(key, initial)
        
        # Increment then decrement
        cache.incr(key, delta)
        result = cache.decr(key, delta)
        
        assert result == initial
        assert cache.get(key) == initial
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test 5: Pop removes items
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.integers()
)
@settings(max_examples=200)
def test_pop_removes_items(key, value):
    """Test that after pop(key), the key is not in cache."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Add item
        cache.set(key, value)
        assert key in cache
        
        # Pop item
        popped = cache.pop(key)
        assert popped == value
        
        # Key should not be in cache anymore
        assert key not in cache
        assert cache.get(key) is None
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test 6: JSONDisk round-trip for JSON-serializable data
@given(
    data=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(max_size=1000),
        st.lists(st.integers(), max_size=100),
        st.dictionaries(st.text(min_size=1, max_size=20), st.integers(), max_size=20)
    )
)
@settings(max_examples=200)
def test_jsondisk_round_trip(data):
    """Test JSONDisk maintains round-trip for JSON-serializable data."""
    tmpdir = tempfile.mkdtemp()
    try:
        # Use JSONDisk for both key and value serialization
        cache = Cache(tmpdir, disk=JSONDisk)
        
        # Use a simple string key
        key = "test_key"
        
        # Store and retrieve value
        cache.set(key, data)
        retrieved = cache.get(key)
        
        # JSONDisk uses JSON serialization, which has some quirks:
        # - Tuples become lists
        # - Some float representations might change slightly
        if isinstance(data, float):
            if math.isnan(data):
                assert math.isnan(retrieved)
            else:
                assert math.isclose(retrieved, data, rel_tol=1e-9, abs_tol=1e-9)
        else:
            assert retrieved == data
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test 7: Cache contains consistency
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.integers()
)
@settings(max_examples=200)
def test_cache_contains_consistency(key, value):
    """Test that if key in cache, then cache.get(key) should not return None."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Initially key should not be in cache
        assert key not in cache
        assert cache.get(key) is None
        
        # After setting, key should be in cache
        cache.set(key, value)
        assert key in cache
        assert cache.get(key) == value
        
        # After deleting, key should not be in cache
        cache.delete(key)
        assert key not in cache
        assert cache.get(key) is None
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    print("Running property-based tests for diskcache.core...")
    
    # Run each test
    test_disk_put_get_round_trip()
    print("✓ Disk put/get round-trip test passed")
    
    test_cache_set_get_consistency()
    print("✓ Cache set/get consistency test passed")
    
    test_cache_add_uniqueness()
    print("✓ Cache add uniqueness test passed")
    
    test_increment_decrement_inverse()
    print("✓ Increment/decrement inverse test passed")
    
    test_pop_removes_items()
    print("✓ Pop removes items test passed")
    
    test_jsondisk_round_trip()
    print("✓ JSONDisk round-trip test passed")
    
    test_cache_contains_consistency()
    print("✓ Cache contains consistency test passed")
    
    print("\nAll tests passed!")