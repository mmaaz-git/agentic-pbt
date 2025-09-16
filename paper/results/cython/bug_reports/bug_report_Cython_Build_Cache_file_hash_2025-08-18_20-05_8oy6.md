# Bug Report: Cython.Build.Cache.file_hash Caching Ignores File Modifications

**Target**: `Cython.Build.Cache.file_hash`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `file_hash` function in Cython.Build.Cache incorrectly caches hash values based solely on filename, returning stale hashes when file contents change.

## Property-Based Test

```python
@given(st.binary(min_size=0, max_size=10000))
def test_file_hash_properties(content):
    """Test that file_hash produces consistent, valid hex hashes."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        path = tmp.name
        
        try:
            hash1 = Cython.Build.Cache.file_hash(path)
            
            # Modify file content
            with open(path, 'wb') as f:
                f.write(content + b'x')
            hash2 = Cython.Build.Cache.file_hash(path)
            
            # Hash should change when content changes
            if content:
                assert hash1 != hash2
                
        finally:
            os.unlink(path)
```

**Failing input**: `content=b'\x00'`

## Reproducing the Bug

```python
import tempfile
import os
import Cython.Build.Cache

with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(b'\x00')
    tmp.flush()
    path = tmp.name
    
    hash1 = Cython.Build.Cache.file_hash(path)
    print(f"Hash before modification: {hash1}")
    
    with open(path, 'wb') as f:
        f.write(b'\x00x')
    
    hash2 = Cython.Build.Cache.file_hash(path)
    print(f"Hash after modification: {hash2}")
    print(f"Bug: Hashes are the same despite different content!")
    
    Cython.Build.Cache.file_hash.cache_clear()
    hash3 = Cython.Build.Cache.file_hash(path)
    print(f"Hash after cache clear: {hash3}")
    print(f"Correct: Hash changed after cache clear")
    
    os.unlink(path)
```

## Why This Is A Bug

The `file_hash` function is decorated with `@cached_function` which caches results based on the filename argument. This violates the fundamental expectation that a file hash function should return different hashes when file contents change. This can lead to incorrect build decisions, stale cache usage, and hard-to-debug compilation issues where Cython fails to detect file modifications.

## Fix

```diff
@cached_function
def file_hash(filename):
+   """
+   WARNING: This function caches based on filename only.
+   It will not detect file content changes during the same session.
+   Consider adding file modification time to the cache key.
+   """
    path = os.path.normpath(filename)
    prefix = ("%d:%s" % (len(path), path)).encode("UTF-8")
    m = hashlib.sha256(prefix)
    with open(path, "rb") as f:
        data = f.read(65000)
        while data:
            m.update(data)
            data = f.read(65000)
    return m.hexdigest()
```

A proper fix would involve modifying the caching mechanism to include file modification time or size in the cache key, or removing caching entirely for this function.