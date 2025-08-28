#!/usr/bin/env python3

import sys
import tempfile
import shutil
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.core import Cache

# Investigate volume tracking issue
tmpdir = tempfile.mkdtemp()
try:
    cache = Cache(tmpdir)
    
    print(f"Initial volume: {cache.volume()}")
    
    # Add a small value
    cache.set("key1", b'\x00' * 100)
    print(f"After adding 100 zero bytes: {cache.volume()}")
    
    # Add another small value
    cache.set("key2", b'\xff' * 100)
    print(f"After adding 100 0xff bytes: {cache.volume()}")
    
    # Add a larger value (should go to file)
    cache.set("key3", b'\x00' * 100000)
    print(f"After adding 100000 zero bytes: {cache.volume()}")
    
    # Check statistics
    stats = cache.stats(enable=True)
    print(f"Cache stats: {stats}")
    
finally:
    cache.close()
    shutil.rmtree(tmpdir)