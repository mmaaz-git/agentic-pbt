#!/usr/bin/env python3
"""Demonstrate the performance impact of the caching bug."""

import os
import time
import pydantic.plugin._loader as loader

def test_caching_behavior():
    """Test that demonstrates the caching bug's impact."""
    
    # Test 1: When plugins are disabled
    print("Test 1: Plugins disabled with '__all__'")
    loader._plugins = None
    loader._loading_plugins = False
    os.environ['PYDANTIC_DISABLE_PLUGINS'] = '__all__'
    
    # First call
    start = time.perf_counter()
    plugins1 = list(loader.get_plugins())
    time1 = time.perf_counter() - start
    
    # Second call - should use cache but doesn't
    start = time.perf_counter()
    plugins2 = list(loader.get_plugins())
    time2 = time.perf_counter() - start
    
    print(f"  First call returned: {plugins1}")
    print(f"  Second call returned: {plugins2}")
    print(f"  _plugins after calls: {loader._plugins}")
    print(f"  Bug: _plugins not cached, environment checked every time")
    
    # Clean up
    del os.environ['PYDANTIC_DISABLE_PLUGINS']
    
    print("\nTest 2: Normal operation (no PYDANTIC_DISABLE_PLUGINS)")
    loader._plugins = None
    loader._loading_plugins = False
    
    # First call - will scan for plugins
    plugins3 = list(loader.get_plugins())
    
    # Second call - uses cache
    plugins4 = list(loader.get_plugins())
    
    print(f"  _plugins after calls: {loader._plugins}")
    print(f"  Correct: _plugins is cached as a dict")
    
    # The bug means that when plugins are disabled:
    # 1. The cache is never set
    # 2. Environment variable is checked on every call
    # 3. This violates the documented caching behavior

if __name__ == "__main__":
    test_caching_behavior()