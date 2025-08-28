#!/usr/bin/env python3
"""Test realistic usage scenarios with large integers"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from srsly._msgpack_api import msgpack_dumps, msgpack_loads

# Test 1: Hash values (commonly large integers)
print("Test 1: Large hash values (common in cryptography)")
try:
    # SHA-256 hash as integer
    sha256_max = 2**256 - 1
    data = {"sha256_hash": sha256_max}
    packed = msgpack_dumps(data)
    print("  SUCCESS: Can serialize SHA-256 sized integers")
except OverflowError as e:
    print(f"  FAILED: Cannot serialize SHA-256 sized integers")
    print(f"    This is problematic for cryptographic applications")

# Test 2: Timestamps in nanoseconds
print("\nTest 2: Timestamps in nanoseconds since epoch")
try:
    # Year 3000 in nanoseconds since epoch
    import time
    future_ns = int(time.time() * 1e9) * 1000  # Way in the future
    data = {"timestamp_ns": future_ns}
    packed = msgpack_dumps(data)
    unpacked = msgpack_loads(packed)
    assert unpacked["timestamp_ns"] == future_ns
    print(f"  SUCCESS: Can handle large timestamps ({future_ns})")
except OverflowError:
    print(f"  FAILED: Cannot handle very large timestamps")

# Test 3: Scientific computing - large factorials
print("\nTest 3: Scientific computing - factorials")
import math
try:
    # 25! is larger than 2^64
    factorial_25 = math.factorial(25)
    print(f"  25! = {factorial_25}")
    print(f"  25! > 2^64? {factorial_25 > 2**64}")
    
    data = {"factorial_25": factorial_25}
    packed = msgpack_dumps(data)
    print("  SUCCESS: Can serialize factorial(25)")
except OverflowError:
    print(f"  FAILED: Cannot serialize factorial(25) = {factorial_25}")