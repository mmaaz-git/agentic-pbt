# Bug Report: pyramid.response.FileIter Silent Data Loss with block_size=0

**Target**: `pyramid.response.FileIter`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

FileIter silently discards all file content when initialized with block_size=0, returning empty results instead of reading the file.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.response import FileIter
from io import BytesIO

@given(
    content=st.binary(min_size=1, max_size=10000),
    block_size=st.integers(min_value=0, max_value=1000)
)
def test_fileiter_preserves_content_any_blocksize(content, block_size):
    """FileIter should preserve file content regardless of block_size value."""
    file_obj = BytesIO(content)
    
    file_iter = FileIter(file_obj, block_size=block_size)
    chunks = list(file_iter)
    result = b''.join(chunks)
    
    assert result == content, \
        f"FileIter with block_size={block_size} lost content. " \
        f"Expected {len(content)} bytes, got {len(result)} bytes"
```

**Failing input**: `content=b'\x00', block_size=0`

## Reproducing the Bug

```python
from io import BytesIO
from pyramid.response import FileIter

content = b"This content should be read"
file_obj = BytesIO(content)

file_iter = FileIter(file_obj, block_size=0)

chunks = list(file_iter)
result = b''.join(chunks)

print(f"Original: {content}")
print(f"Result:   {result}")
print(f"Data lost: {content != result}")
```

## Why This Is A Bug

FileIter is documented as "A fixed-block-size iterator for use as a WSGI app_iter" that reads from a file object. When block_size=0, the iterator calls `file.read(0)` which returns empty bytes `b''`. The code then checks `if not val:` which evaluates to True for empty bytes, causing immediate StopIteration without reading any file content. This silently discards all data without raising an error, which could lead to data loss in production systems.

## Fix

```diff
--- a/pyramid/response.py
+++ b/pyramid/response.py
@@ -80,6 +80,8 @@ class FileIter:
 
     def __init__(self, file, block_size=_BLOCK_SIZE):
         self.file = file
+        if block_size <= 0:
+            raise ValueError(f"block_size must be positive, got {block_size}")
         self.block_size = block_size
 
     def __iter__(self):
```