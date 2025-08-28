#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib
import zlib

# This works with standard zlib
data = b"Hello, World!"
zlib_compressed = zlib.compress(data, level=-1)
print(f"Standard zlib with level=-1: Success")

# This fails with isal_zlib
try:
    isal_compressed = isal_zlib.compress(data, level=-1)
    print(f"isal_zlib with level=-1: Success")
except Exception as e:
    print(f"isal_zlib with level=-1: Failed - {e}")

# Also, the Z_DEFAULT_COMPRESSION constant is incompatible
print(f"\nConstants mismatch:")
print(f"  zlib.Z_DEFAULT_COMPRESSION = {zlib.Z_DEFAULT_COMPRESSION}")
print(f"  isal_zlib.Z_DEFAULT_COMPRESSION = {isal_zlib.Z_DEFAULT_COMPRESSION}")
print(f"  These should be equal for compatibility, but they're not!")