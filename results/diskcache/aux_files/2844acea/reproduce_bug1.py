#!/usr/bin/env python3
"""Minimal reproduction of diskcache incr() bug with large integers."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import tempfile
from diskcache import Cache

# Bug 1: Large integers get stored as bytes, causing TypeError when incrementing
with tempfile.TemporaryDirectory() as tmpdir:
    cache = Cache(tmpdir)
    
    # Set a large integer value (2^63, just beyond SQLite's integer range)
    large_int = 9_223_372_036_854_775_808  # 2^63
    cache.set('key', large_int)
    
    # Try to increment - this fails with TypeError
    try:
        cache.incr('key', 1)
        print("No error - bug may be fixed")
    except TypeError as e:
        print(f"Bug reproduced: {e}")
        print(f"Error: can't increment large integer {large_int}")


# Bug 2: Overflow when incrementing causes OverflowError
with tempfile.TemporaryDirectory() as tmpdir:
    cache = Cache(tmpdir)
    
    # Set a value close to SQLite's max integer
    near_max = 9_223_372_036_854_775_700
    cache.set('key', near_max)
    
    # Try to increment beyond SQLite's range
    try:
        cache.incr('key', 200)
        print("No error - bug may be fixed")
    except OverflowError as e:
        print(f"\nBug reproduced: {e}")
        print(f"Error: incrementing {near_max} by 200 exceeds SQLite INTEGER limit")