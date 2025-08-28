#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_lib as igzip_lib

# Test with non-empty data
data = b'Hello'
compressed = igzip_lib.compress(data)
print(f"Original data: {data!r}")
print(f"Compressed: {compressed!r}")

decompressor = igzip_lib.IgzipDecompressor()

# Decompress all data
result = decompressor.decompress(compressed)
print(f"Decompressed: {result!r}")
print(f"Decompressor EOF: {decompressor.eof}")

# Try to decompress again after EOF - should not raise EOFError
print("\nAttempting to decompress after EOF reached...")
try:
    extra = decompressor.decompress(b'')
    print(f"Extra result: {extra!r}")
    print("SUCCESS: No error")
except EOFError as e:
    print(f"ERROR: EOFError raised: {e}")
    print("This is a bug - decompress should return empty bytes after EOF, not raise EOFError")

# Compare with zlib
print("\n--- Comparison with standard zlib ---")
import zlib

zlib_compressed = zlib.compress(data)
zlib_decompressor = zlib.decompressobj()

zlib_result = zlib_decompressor.decompress(zlib_compressed)
print(f"zlib result: {zlib_result!r}")
print(f"zlib EOF: {zlib_decompressor.eof}")

# zlib doesn't raise EOFError
zlib_extra = zlib_decompressor.decompress(b'')
print(f"zlib extra: {zlib_extra!r}")
print("zlib correctly returns empty bytes without error")