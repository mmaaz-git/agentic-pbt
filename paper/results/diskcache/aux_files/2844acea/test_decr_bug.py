#!/usr/bin/env python3
"""Test if decr() has the same bug as incr() with large integers."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import tempfile
from diskcache import Cache

# Test decr() with large integers
with tempfile.TemporaryDirectory() as tmpdir:
    cache = Cache(tmpdir)
    
    # Set a large integer value (2^63, just beyond SQLite's integer range)
    large_int = 9_223_372_036_854_775_808  # 2^63
    cache.set('key', large_int)
    
    # Try to decrement - this should fail with TypeError like incr()
    try:
        result = cache.decr('key', 1)
        print(f"No error - decr handled large int correctly: {result}")
    except TypeError as e:
        print(f"Bug confirmed in decr(): {e}")
        print(f"Error: can't decrement large integer {large_int}")