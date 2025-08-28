#!/usr/bin/env python
"""Check for potential bugs in FanoutCache by direct testing."""

import tempfile
import shutil
from diskcache import FanoutCache

def test_transaction_atomicity():
    """Test if transactions are truly atomic across shards."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    cache = FanoutCache(directory=temp_dir, shards=4)
    
    try:
        # Set up initial values across different shards
        # We need keys that hash to different shards
        keys = []
        for i in range(100):
            key = f"key_{i}"
            shard_idx = cache._hash(key) % cache._count
            if len(keys) < cache._count and shard_idx == len(keys):
                keys.append(key)
                cache[key] = 0
            if len(keys) == cache._count:
                break
        
        print(f"Testing with keys: {keys}")
        
        # Try concurrent-like operations
        with cache.transact():
            for key in keys:
                cache.incr(key, delta=1)
        
        # Check all incremented
        for key in keys:
            val = cache[key]
            print(f"{key}: {val}")
            assert val == 1, f"Expected 1, got {val}"
        
        print("Transaction atomicity test passed")
        
    finally:
        cache.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_stats_accuracy():
    """Test if stats are accurately tracked."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    cache = FanoutCache(directory=temp_dir, shards=4)
    
    try:
        # Enable stats
        cache.stats(enable=True, reset=True)
        
        # Perform operations
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        
        # Generate hits
        _ = cache.get("key1")
        _ = cache.get("key2")
        
        # Generate misses
        _ = cache.get("nonexistent1", default=None)
        _ = cache.get("nonexistent2", default=None)
        
        # Check stats
        total_hits, total_misses = cache.stats()
        print(f"Total hits: {total_hits}, Total misses: {total_misses}")
        
        # Manually sum shard stats
        shard_hits = 0
        shard_misses = 0
        for i, shard in enumerate(cache._shards):
            h, m = shard.stats()
            print(f"Shard {i}: hits={h}, misses={m}")
            shard_hits += h
            shard_misses += m
        
        assert total_hits == shard_hits, f"Hit mismatch: {total_hits} != {shard_hits}"
        assert total_misses == shard_misses, f"Miss mismatch: {total_misses} != {shard_misses}"
        
        print("Stats accuracy test passed")
        
    finally:
        cache.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_clear_count_bug():
    """Test if clear returns correct count."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    cache = FanoutCache(directory=temp_dir, shards=4)
    
    try:
        # Add items - try to spread across shards
        items_added = 0
        for i in range(20):
            key = f"test_key_{i}"
            cache[key] = f"value_{i}"
            items_added += 1
        
        print(f"Added {items_added} items")
        print(f"Cache length: {len(cache)}")
        
        # Clear and check count
        cleared_count = cache.clear()
        print(f"Clear returned: {cleared_count}")
        
        # Verify
        assert cleared_count == items_added, f"Clear count mismatch: returned {cleared_count}, expected {items_added}"
        assert len(cache) == 0, f"Cache not empty after clear: {len(cache)}"
        
        print("Clear count test passed")
        
    finally:
        cache.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_iteration_duplicates():
    """Test if iteration has duplicates."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    cache = FanoutCache(directory=temp_dir, shards=4)
    
    try:
        # Add items
        keys_added = set()
        for i in range(10):
            key = f"key_{i}"
            cache[key] = f"value_{i}"
            keys_added.add(key)
        
        # Iterate and collect
        keys_iterated = list(cache)
        
        print(f"Added {len(keys_added)} keys")
        print(f"Iterated {len(keys_iterated)} keys")
        print(f"Unique iterated: {len(set(keys_iterated))}")
        
        # Check for duplicates
        if len(keys_iterated) != len(set(keys_iterated)):
            duplicates = [k for k in keys_iterated if keys_iterated.count(k) > 1]
            print(f"DUPLICATES FOUND: {duplicates}")
            raise AssertionError(f"Iteration produced duplicates: {duplicates}")
        
        # Check all keys present
        assert set(keys_iterated) == keys_added
        
        print("Iteration test passed")
        
    finally:
        cache.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_volume_calculation():
    """Test if volume is calculated correctly."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    cache = FanoutCache(directory=temp_dir, shards=4)
    
    try:
        # Add items
        for i in range(10):
            cache[f"key_{i}"] = "x" * 1000  # 1KB values
        
        total_volume = cache.volume()
        
        # Sum individual volumes
        shard_volume_sum = sum(shard.volume() for shard in cache._shards)
        
        print(f"Total volume: {total_volume}")
        print(f"Sum of shard volumes: {shard_volume_sum}")
        
        assert total_volume == shard_volume_sum, f"Volume mismatch: {total_volume} != {shard_volume_sum}"
        
        print("Volume calculation test passed")
        
    finally:
        cache.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Running direct bug checks...")
    print("="*60)
    
    try:
        test_transaction_atomicity()
        test_stats_accuracy()
        test_clear_count_bug()
        test_iteration_duplicates()
        test_volume_calculation()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()