#!/usr/bin/env python
"""Simple test to check if we can run at all."""

try:
    from diskcache import FanoutCache
    print("Successfully imported FanoutCache")
    
    # Create a simple cache
    cache = FanoutCache(shards=2)
    
    # Test basic operations
    cache["key1"] = "value1"
    result = cache["key1"]
    assert result == "value1"
    print("Basic set/get test passed")
    
    # Test the sharding
    index1 = cache._hash("key1") % cache._count
    index2 = cache._hash("key2") % cache._count
    print(f"key1 maps to shard {index1}")
    print(f"key2 maps to shard {index2}")
    
    cache.close()
    print("All basic tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()