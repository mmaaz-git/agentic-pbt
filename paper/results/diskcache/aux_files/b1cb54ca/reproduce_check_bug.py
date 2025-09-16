"""Reproduce the check() return type issue in diskcache."""

import sys
import tempfile
import shutil

# Add the diskcache path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

import diskcache

# Create a temporary cache directory
cache_dir = tempfile.mkdtemp(prefix='test-diskcache-')

try:
    cache = diskcache.Cache(cache_dir)
    
    # Add an item
    cache.set('0', '')
    
    # Check should pass for a valid cache
    warnings_count = cache.check()
    print(f"cache.check() returned: {warnings_count!r}")
    print(f"Type: {type(warnings_count)}")
    print(f"Expected: 0 (int)")
    
    cache.close()
finally:
    shutil.rmtree(cache_dir, ignore_errors=True)