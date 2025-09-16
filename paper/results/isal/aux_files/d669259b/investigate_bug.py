#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib

# Test different compression levels
data = b"Hello, World!"

print("Testing compression levels:")
for level in [-2, -1, 0, 1, 2, 3, 4, 5]:
    try:
        compressed = isal_zlib.compress(data, level=level)
        print(f"  Level {level}: Success (compressed size: {len(compressed)})")
    except Exception as e:
        print(f"  Level {level}: Failed - {type(e).__name__}: {e}")

print("\nTesting with empty data:")
empty_data = b""
for level in [-2, -1, 0, 1, 2, 3, 4, 5]:
    try:
        compressed = isal_zlib.compress(empty_data, level=level)
        print(f"  Level {level}: Success (compressed size: {len(compressed)})")
    except Exception as e:
        print(f"  Level {level}: Failed - {type(e).__name__}: {e}")

print("\nComparing with standard zlib:")
import zlib
for level in [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
    try:
        compressed = zlib.compress(data, level=level)
        print(f"  zlib level {level}: Success")
    except Exception as e:
        print(f"  zlib level {level}: Failed - {e}")