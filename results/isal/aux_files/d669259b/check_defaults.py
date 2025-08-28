#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib
import zlib

print("Default compression constants:")
print(f"isal_zlib.ISAL_DEFAULT_COMPRESSION: {isal_zlib.ISAL_DEFAULT_COMPRESSION}")
print(f"isal_zlib.Z_DEFAULT_COMPRESSION: {isal_zlib.Z_DEFAULT_COMPRESSION}")
print(f"zlib.Z_DEFAULT_COMPRESSION: {zlib.Z_DEFAULT_COMPRESSION}")

print("\nValid compression levels according to docstring:")
print(isal_zlib.compress.__doc__)

print("\nCheck if Z_DEFAULT_COMPRESSION == -1:")
print(f"isal_zlib.Z_DEFAULT_COMPRESSION == -1: {isal_zlib.Z_DEFAULT_COMPRESSION == -1}")
print(f"zlib.Z_DEFAULT_COMPRESSION == -1: {zlib.Z_DEFAULT_COMPRESSION == -1}")

print("\nTrying to use Z_DEFAULT_COMPRESSION with isal:")
data = b"test"
try:
    compressed = isal_zlib.compress(data, level=isal_zlib.Z_DEFAULT_COMPRESSION)
    print(f"Success with Z_DEFAULT_COMPRESSION ({isal_zlib.Z_DEFAULT_COMPRESSION})")
except Exception as e:
    print(f"Failed with Z_DEFAULT_COMPRESSION ({isal_zlib.Z_DEFAULT_COMPRESSION}): {e}")

print("\nTrying standard zlib with -1:")
try:
    compressed = zlib.compress(data, level=-1)
    print("zlib succeeds with level=-1")
except Exception as e:
    print(f"zlib fails with level=-1: {e}")