#!/usr/bin/env python3
"""Minimal reproduction of integer overflow bug in srsly.msgpack"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from srsly._msgpack_api import msgpack_dumps, msgpack_loads

# Test 1: Unsigned integer overflow
print("Test 1: Unsigned integer overflow")
try:
    large_unsigned = 2**64  # 18446744073709551616
    data = {"value": large_unsigned}
    print(f"  Trying to serialize: {large_unsigned}")
    packed = msgpack_dumps(data)
    print("  SUCCESS: Serialized without error")
except OverflowError as e:
    print(f"  FAILED: {e}")

# Test 2: Negative integer overflow  
print("\nTest 2: Negative integer overflow")
try:
    large_negative = -(2**63) - 1  # -9223372036854775809
    data = {"value": large_negative}
    print(f"  Trying to serialize: {large_negative}")
    packed = msgpack_dumps(data)
    print("  SUCCESS: Serialized without error")
except OverflowError as e:
    print(f"  FAILED: {e}")

# Test 3: Edge cases that should work
print("\nTest 3: Edge cases (should work)")
try:
    max_int64 = 2**63 - 1  # 9223372036854775807
    min_int64 = -(2**63)   # -9223372036854775808
    max_uint64 = 2**64 - 1 # 18446744073709551615
    
    data = {
        "max_int64": max_int64,
        "min_int64": min_int64,
        "max_uint64": max_uint64
    }
    print(f"  max_int64: {max_int64}")
    print(f"  min_int64: {min_int64}")
    print(f"  max_uint64: {max_uint64}")
    
    packed = msgpack_dumps(data)
    unpacked = msgpack_loads(packed)
    
    for key in data:
        if unpacked[key] == data[key]:
            print(f"  {key}: SUCCESS")
        else:
            print(f"  {key}: FAILED (got {unpacked[key]})")
            
except Exception as e:
    print(f"  FAILED: {e}")

# Test 4: Python's arbitrary precision integers
print("\nTest 4: Very large integers (Python arbitrary precision)")
try:
    huge_int = 2**100
    data = {"huge": huge_int}
    print(f"  Trying to serialize 2^100: {huge_int}")
    packed = msgpack_dumps(data)
    print("  SUCCESS: Serialized without error")
except OverflowError as e:
    print(f"  FAILED: {e}")