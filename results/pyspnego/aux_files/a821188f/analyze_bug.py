"""Analyze the root cause of the bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from spnego.channel_bindings import _pack_value, _unpack_value, AddressType
import struct

# Test how _pack_value handles None
print("Testing _pack_value with None:")
packed_none = _pack_value(AddressType.unspecified, None)
print(f"  _pack_value(AddressType.unspecified, None) = {packed_none!r}")

# This should be: addr_type (4 bytes) + length (4 bytes, should be 0) + data (0 bytes)
print(f"  Length encoded in packed data: {struct.unpack('<I', packed_none[4:8])[0]}")

# Now test unpacking
print("\nTesting _unpack_value:")
b_mem = memoryview(packed_none)
# Skip the address type (first 4 bytes)
data, offset = _unpack_value(b_mem, 4)
print(f"  Unpacked data: {data!r}")
print(f"  Type: {type(data)}")

# The issue is in _pack_value line 12:
# if not b:
#     b = b""
# This converts None to b"", and unpack can't distinguish between them

print("\nRoot cause:")
print("  In _pack_value (line 11-12), None is converted to b''")
print("  In _unpack_value, b'' is returned as-is")
print("  There's no way to distinguish between None and b'' after packing")

# Test with actual empty bytes
print("\nTesting with actual empty bytes:")
bindings_empty = _pack_value(AddressType.unspecified, b'')
print(f"  _pack_value(AddressType.unspecified, b'') = {bindings_empty!r}")
print(f"  Same as None? {bindings_empty == packed_none}")