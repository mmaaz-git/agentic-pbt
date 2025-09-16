#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib
import inspect

# Let's examine the functions in detail
functions = ['compress', 'decompress', 'adler32', 'crc32', 'compressobj', 'decompressobj']

for fname in functions:
    func = getattr(isal_zlib, fname)
    print(f"\n{fname}:")
    print(f"  Signature: {inspect.signature(func) if hasattr(inspect, 'signature') else 'N/A'}")
    print(f"  Docstring: {func.__doc__}")
    print("-" * 40)

# Test basic compress/decompress to see if they work
test_data = b"Hello, World!"
compressed = isal_zlib.compress(test_data)
decompressed = isal_zlib.decompress(compressed)
print(f"\nBasic test:")
print(f"  Original: {test_data}")
print(f"  Compressed: {compressed[:20]}... (len={len(compressed)})")
print(f"  Decompressed: {decompressed}")
print(f"  Round-trip successful: {test_data == decompressed}")

# Check if it's compatible with standard zlib
import zlib
std_compressed = zlib.compress(test_data)
isal_decompressed = isal_zlib.decompress(std_compressed)
print(f"\nCross-compatibility test:")
print(f"  Standard zlib compressed, isal decompressed: {isal_decompressed}")
print(f"  Compatible: {test_data == isal_decompressed}")