# Bug Report: isal.igzip_threaded Flush Creates Invalid Gzip Stream

**Target**: `isal.igzip_threaded._ThreadedGzipWriter`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_ThreadedGzipWriter.flush()` method can produce invalid gzip streams when specific data patterns are written before the flush operation, resulting in corrupted files that cannot be decompressed.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import isal.igzip_threaded as igzip_threaded
import tempfile
import os

@given(
    chunks=st.lists(st.binary(min_size=0, max_size=100), min_size=0, max_size=20),
    threads=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30)
def test_write_after_flush(chunks, threads):
    """Test that writing after flush works correctly."""
    if not chunks:
        return
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            for i, chunk in enumerate(chunks):
                f.write(chunk)
                if i % 3 == 0:  # Flush every 3rd write
                    f.flush()
        
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
        
        assert recovered == b''.join(chunks)
    finally:
        os.unlink(tmp_path)
```

**Failing input**: `chunks=[b'\x00', b'\x00\x00\x00\x00'], threads=1`

## Reproducing the Bug

```python
import tempfile
import os
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')
import isal.igzip_threaded as igzip_threaded

chunks = [b'\x00', b'\x00\x00\x00\x00']

with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp_path = tmp.name

try:
    with igzip_threaded.open(tmp_path, "wb", threads=1) as f:
        f.write(chunks[0])
        f.flush()
        f.write(chunks[1])
    
    with igzip_threaded.open(tmp_path, "rb") as f:
        recovered = f.read()
        print(f"Success: {recovered}")
except Exception as e:
    print(f"Error: {e}")
finally:
    os.unlink(tmp_path)
```

## Why This Is A Bug

The flush() method is intended to end the current gzip stream and start a new one, creating concatenated gzip streams that should be readable. However, when specific small data patterns (like a single null byte) are written before flush(), the resulting file becomes corrupted with "Invalid lookback distance" errors during decompression. This violates the expected behavior that flush() should create valid concatenated gzip streams.

## Fix

The issue appears to be in the `_end_gzip_stream` method which writes an empty deflate block after flushing all queues. The problem occurs when very small amounts of data create edge cases in the compression state. A potential fix would be to ensure proper handling of minimal data before creating the empty deflate block:

```diff
--- a/isal/igzip_threaded.py
+++ b/isal/igzip_threaded.py
@@ -319,6 +319,10 @@ class _ThreadedGzipWriter(io.RawIOBase):
     def _end_gzip_stream(self):
         self._check_closed()
         # Wait for all data to be compressed
+        # Ensure at least one block has been written
+        if self.index == 0:
+            # Write an empty block to ensure valid stream
+            self.write(b'')
         for in_q in self.input_queues:
             in_q.join()
         # Wait for all data to be written
```

Alternatively, the issue may be in how the compressor handles the dictionary reference when very small amounts of data are compressed with subsequent flush operations. Further investigation of the `_ParallelCompress.compress_and_crc` method's handling of small data with dictionary references would be needed for a complete fix.