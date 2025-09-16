# Bug Report: isal.igzip_lib IgzipDecompressor Raises EOFError After EOF

**Target**: `isal.igzip_lib.IgzipDecompressor`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

IgzipDecompressor.decompress() incorrectly raises EOFError when called after EOF is reached, while the standard zlib behavior is to return empty bytes.

## Property-Based Test

```python
@given(st.binary(min_size=0, max_size=10000))
@settings(max_examples=200)
def test_decompressor_max_length_parameter(data):
    compressed = igzip_lib.compress(data)
    
    decompressor = igzip_lib.IgzipDecompressor()
    
    # Decompress with max_length limit
    max_len = min(10, len(data))
    partial = decompressor.decompress(compressed, max_length=max_len)
    assert len(partial) <= max_len
    
    # Decompress the rest
    rest = decompressor.decompress(b'', max_length=-1)
    assert partial + rest == data
```

**Failing input**: `data=b''`

## Reproducing the Bug

```python
import isal.igzip_lib as igzip_lib

data = b''
compressed = igzip_lib.compress(data)

decompressor = igzip_lib.IgzipDecompressor()
partial = decompressor.decompress(compressed, max_length=0)
print(f"EOF reached: {decompressor.eof}")  # True

# This raises EOFError, but should return b''
rest = decompressor.decompress(b'', max_length=-1)
```

## Why This Is A Bug

The IgzipDecompressor behavior is inconsistent with Python's standard zlib.decompressobj(), which returns empty bytes when decompress() is called after EOF. This violates the principle of least surprise and makes IgzipDecompressor incompatible as a drop-in replacement for zlib's decompressor.

## Fix

The IgzipDecompressor.decompress() method should check if EOF has been reached and return empty bytes instead of raising EOFError, matching the standard zlib behavior:

```diff
def decompress(self, data, max_length=-1):
+   if self.eof and not data:
+       return b''
    # existing decompression logic
```