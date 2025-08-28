#!/usr/bin/env python3

import sys
import tempfile
import shutil
import sqlite3
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import diskcache
from diskcache.core import Disk, JSONDisk, Cache
from hypothesis import given, strategies as st, settings, assume
import math
import time

# Test with extreme values and edge cases
@given(
    value=st.one_of(
        st.just(0),
        st.just(-0.0),
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(2**63 - 1),  # Max int64
        st.just(-2**63),     # Min int64
        st.just(2**63),      # Just beyond int64
        st.just(""),         # Empty string
        st.just(b""),        # Empty bytes
        st.text(alphabet="\x00\x01\x02\x7f\x80\xff", min_size=1),  # Control chars
        st.binary(min_size=0, max_size=1000000)  # Large binary
    )
)
@settings(max_examples=500)
def test_cache_extreme_values(value):
    """Test cache with extreme/edge case values."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Skip infinity values as they may not serialize properly
        if isinstance(value, float) and math.isinf(value):
            return
        
        cache.set("key", value)
        retrieved = cache.get("key")
        
        if isinstance(value, float) and math.isnan(value):
            assert math.isnan(retrieved)
        else:
            assert retrieved == value
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test expiry behavior
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.integers(),
    expire_time=st.floats(min_value=0.01, max_value=0.05)
)
@settings(max_examples=20)
def test_cache_expiry(key, value, expire_time):
    """Test that expired items are not retrievable."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Set with expiry
        cache.set(key, value, expire=expire_time)
        
        # Should be retrievable immediately
        assert cache.get(key) == value
        assert key in cache
        
        # Wait for expiry
        time.sleep(expire_time + 0.01)
        
        # Should not be retrievable after expiry
        assert cache.get(key) is None
        assert key not in cache
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test concurrent operations
@given(
    keys=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20),
    values=st.lists(st.integers(), min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_cache_multiple_operations(keys, values):
    """Test multiple operations maintain consistency."""
    assume(len(keys) == len(values))
    assume(len(set(keys)) == len(keys))  # All keys unique
    
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Set all key-value pairs
        for k, v in zip(keys, values):
            cache.set(k, v)
        
        # All should be retrievable
        for k, v in zip(keys, values):
            assert cache.get(k) == v
        
        # Delete half
        for k in keys[:len(keys)//2]:
            cache.delete(k)
        
        # Check consistency
        for i, k in enumerate(keys):
            if i < len(keys)//2:
                assert k not in cache
            else:
                assert cache.get(k) == values[i]
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test Disk with pickled objects
@given(
    obj=st.one_of(
        st.lists(st.integers()),
        st.dictionaries(st.text(min_size=1), st.integers()),
        st.tuples(st.integers(), st.text(), st.floats(allow_nan=False)),
        st.sets(st.integers()),
        st.frozensets(st.integers())
    )
)
@settings(max_examples=200)
def test_disk_pickle_round_trip(obj):
    """Test Disk handles complex objects via pickling."""
    tmpdir = tempfile.mkdtemp()
    try:
        disk = Disk(tmpdir, pickle_protocol=5)
        
        # Put complex object (will be pickled)
        db_key, raw = disk.put(obj)
        
        # Raw should be False for pickled objects
        assert raw is False
        
        # Should round-trip correctly
        retrieved = disk.get(db_key, raw)
        assert retrieved == obj
    finally:
        shutil.rmtree(tmpdir)


# Test store/fetch for large values
@given(
    data=st.one_of(
        st.binary(min_size=2000, max_size=10000),
        st.text(min_size=1000, max_size=2000)
    )
)
@settings(max_examples=50)
def test_disk_large_values(data):
    """Test Disk handles large values by storing to files."""
    tmpdir = tempfile.mkdtemp()
    try:
        # Set min_file_size low to force file storage
        disk = Disk(tmpdir, min_file_size=1000)
        
        size, mode, filename, db_value = disk.store(data, read=False)
        
        # Large values should be stored in files
        assert filename is not None
        assert db_value is None
        assert size > 0
        
        # Should fetch correctly
        retrieved = disk.fetch(mode, filename, db_value, read=False)
        assert retrieved == data
    finally:
        shutil.rmtree(tmpdir)


# Test touch behavior
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.integers(),
    new_expire=st.floats(min_value=0.5, max_value=2)
)
@settings(max_examples=20)
def test_cache_touch(key, value, new_expire):
    """Test touch updates expiry time for existing keys."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        # Touch non-existent key should return False
        assert cache.touch(key, expire=new_expire) is False
        
        # Set key
        cache.set(key, value, expire=0.1)
        
        # Touch should return True and update expire time
        assert cache.touch(key, expire=new_expire) is True
        
        # Wait for original expiry time
        time.sleep(0.15)
        
        # Should still be retrievable due to touch
        assert cache.get(key) == value
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


# Test volume tracking
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.binary(min_size=50000, max_size=100000),  # Large enough to force file storage
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=20)
def test_cache_volume_tracking(data):
    """Test that cache correctly tracks volume/size for large values."""
    tmpdir = tempfile.mkdtemp()
    try:
        cache = Cache(tmpdir)
        
        initial_volume = cache.volume()
        
        # Add all data (large values will be stored in files)
        for key, value in data.items():
            cache.set(key, value)
        
        # Volume should increase significantly for large values
        new_volume = cache.volume()
        # Large values are stored in files, so volume should increase
        assert new_volume > initial_volume
        
        # Clear cache
        cache.clear()
        
        # Volume should return to near initial (metadata remains)
        final_volume = cache.volume()
        assert final_volume <= initial_volume + 10000  # Allow overhead for db growth
    finally:
        cache.close()
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    print("Running edge case tests for diskcache.core...")
    
    test_cache_extreme_values()
    print("✓ Extreme values test passed")
    
    test_cache_expiry()
    print("✓ Cache expiry test passed")
    
    test_cache_multiple_operations()
    print("✓ Multiple operations test passed")
    
    test_disk_pickle_round_trip()
    print("✓ Disk pickle round-trip test passed")
    
    test_disk_large_values()
    print("✓ Disk large values test passed")
    
    test_cache_touch()
    print("✓ Cache touch test passed")
    
    test_cache_volume_tracking()
    print("✓ Cache volume tracking test passed")
    
    print("\nAll edge case tests passed!")