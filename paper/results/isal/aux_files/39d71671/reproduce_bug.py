#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_lib as igzip_lib

# Minimal reproduction of the bug
data = b''
compressed = igzip_lib.compress(data)
print(f"Original data: {data!r}")
print(f"Compressed: {compressed!r}")

decompressor = igzip_lib.IgzipDecompressor()

# First decompress with max_length
max_len = min(10, len(data))  # max_len = 0 for empty data
print(f"Max length: {max_len}")

partial = decompressor.decompress(compressed, max_length=max_len)
print(f"Partial result: {partial!r}")
print(f"Decompressor EOF: {decompressor.eof}")

# Try to decompress the rest - this should not raise EOFError
try:
    rest = decompressor.decompress(b'', max_length=-1)
    print(f"Rest: {rest!r}")
    print("SUCCESS: No error")
except EOFError as e:
    print(f"ERROR: EOFError raised: {e}")
    print("This is unexpected - decompress should return empty bytes, not raise EOFError")

# Compare with standard zlib behavior
print("\n--- Comparison with standard zlib ---")
import zlib

zlib_compressed = zlib.compress(data)
zlib_decompressor = zlib.decompressobj()

zlib_partial = zlib_decompressor.decompress(zlib_compressed, max_len)
print(f"zlib partial: {zlib_partial!r}")
print(f"zlib unconsumed_tail: {zlib_decompressor.unconsumed_tail!r}")

# zlib doesn't raise EOFError, just returns empty bytes
zlib_rest = zlib_decompressor.decompress(b'')
print(f"zlib rest: {zlib_rest!r}")
print(f"zlib eof: {zlib_decompressor.eof}")