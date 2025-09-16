"""Reproduce the delete idempotency bug in diskcache."""

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
    
    # Set a value
    cache.set('0', '')
    
    # Verify it's there
    print(f"Initial get('0'): {cache.get('0')!r}")
    
    # Delete it
    deleted1 = cache.delete('0')
    print(f"First delete('0'): {deleted1}")
    
    # Now it should return default (None)
    print(f"After delete get('0'): {cache.get('0')!r}")
    
    # Deleting again - according to docstring should be idempotent
    deleted2 = cache.delete('0')
    print(f"Second delete('0'): {deleted2}")
    print(f"Expected: True, Got: {deleted2}")
    
    cache.close()
finally:
    shutil.rmtree(cache_dir, ignore_errors=True)