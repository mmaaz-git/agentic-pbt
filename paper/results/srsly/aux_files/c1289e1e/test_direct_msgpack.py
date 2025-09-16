#!/usr/bin/env python3
"""Test if the bug is in srsly or the underlying msgpack library"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.msgpack as msgpack

# Test the underlying msgpack library directly
print("Testing underlying msgpack library directly:")

# Test 1: Large unsigned integer
print("\nTest 1: Unsigned integer overflow (2^64)")
try:
    large_unsigned = 2**64  
    data = {"value": large_unsigned}
    packed = msgpack.packb(data)
    print("  SUCCESS: Packed without error")
    unpacked = msgpack.unpackb(packed)
    print(f"  Unpacked: {unpacked}")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 2: Large negative integer
print("\nTest 2: Negative integer overflow (-(2^63) - 1)")
try:
    large_negative = -(2**63) - 1
    data = {"value": large_negative}
    packed = msgpack.packb(data)
    print("  SUCCESS: Packed without error")
    unpacked = msgpack.unpackb(packed)
    print(f"  Unpacked: {unpacked}")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 3: Check if strict_types parameter helps
print("\nTest 3: Using strict_types=False")
try:
    large_unsigned = 2**64
    data = {"value": large_unsigned}
    packed = msgpack.packb(data, strict_types=False)
    print("  SUCCESS: Packed without error")
    unpacked = msgpack.unpackb(packed)
    print(f"  Unpacked: {unpacked}")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 4: Check documentation/spec limits
print("\nMsgPack specification integer limits:")
print("  int8:  -128 to 127")
print("  int16: -32768 to 32767")
print("  int32: -2147483648 to 2147483647")
print("  int64: -9223372036854775808 to 9223372036854775807")
print("  uint8:  0 to 255")
print("  uint16: 0 to 65535")
print("  uint32: 0 to 4294967295")
print("  uint64: 0 to 18446744073709551615")
print("\nIntegers outside these ranges are NOT supported by the msgpack specification.")