#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_lib as igzip_lib
import inspect

# Test the functions exist and get their docstrings
print("compress function:")
print(f"  Signature: compress(data, level={igzip_lib.ISAL_DEFAULT_COMPRESSION}, flag={igzip_lib.COMP_DEFLATE}, mem_level={igzip_lib.MEM_LEVEL_DEFAULT}, hist_bits={igzip_lib.MAX_HIST_BITS})")
if hasattr(igzip_lib.compress, '__doc__'):
    print(f"  Docstring: {igzip_lib.compress.__doc__}")
print()

print("decompress function:")
print(f"  Signature: decompress(data, flag={igzip_lib.DECOMP_DEFLATE}, hist_bits={igzip_lib.MAX_HIST_BITS}, bufsize={igzip_lib.DEF_BUF_SIZE})")
if hasattr(igzip_lib.decompress, '__doc__'):
    print(f"  Docstring: {igzip_lib.decompress.__doc__}")
print()

print("IgzipDecompressor class:")
if hasattr(igzip_lib.IgzipDecompressor, '__doc__'):
    print(f"  Docstring: {igzip_lib.IgzipDecompressor.__doc__}")

# Get constant values
print("\nConstant values:")
print(f"  ISAL_DEFAULT_COMPRESSION = {igzip_lib.ISAL_DEFAULT_COMPRESSION}")
print(f"  ISAL_BEST_SPEED = {igzip_lib.ISAL_BEST_SPEED}")
print(f"  ISAL_BEST_COMPRESSION = {igzip_lib.ISAL_BEST_COMPRESSION}")
print(f"  COMP_DEFLATE = {igzip_lib.COMP_DEFLATE}")
print(f"  COMP_GZIP = {igzip_lib.COMP_GZIP}")
print(f"  COMP_ZLIB = {igzip_lib.COMP_ZLIB}")
print(f"  DECOMP_DEFLATE = {igzip_lib.DECOMP_DEFLATE}")
print(f"  DECOMP_GZIP = {igzip_lib.DECOMP_GZIP}")
print(f"  DECOMP_ZLIB = {igzip_lib.DECOMP_ZLIB}")
print(f"  MAX_HIST_BITS = {igzip_lib.MAX_HIST_BITS}")
print(f"  DEF_BUF_SIZE = {igzip_lib.DEF_BUF_SIZE}")

# Test basic round-trip
print("\nQuick test:")
test_data = b"Hello, World! " * 100
compressed = igzip_lib.compress(test_data)
decompressed = igzip_lib.decompress(compressed)
print(f"Round-trip test: {decompressed == test_data}")