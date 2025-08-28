#!/usr/bin/env python3
"""Check if there's supposed to be a fallback for large integers"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from srsly._msgpack_api import msgpack_dumps, msgpack_loads
import srsly.msgpack as msgpack

# Check if using default parameter helps
print("Test: Using default parameter to handle large integers")

def custom_encoder(obj):
    """Custom encoder to handle large integers as strings"""
    if isinstance(obj, int) and (obj > 2**63-1 or obj < -(2**63)):
        return {"__bigint__": str(obj)}
    raise TypeError(f"Object of type {type(obj)} is not serializable")

try:
    large_int = 2**100
    data = {"value": large_int}
    
    # Try with custom default handler
    packer = msgpack.Packer(default=custom_encoder)
    packed = packer.pack(data)
    print(f"  SUCCESS: Packed large integer using custom encoder")
    
    # Now unpack
    unpacked = msgpack.unpackb(packed)
    print(f"  Unpacked: {unpacked}")
    
except Exception as e:
    print(f"  FAILED: {e}")

# Check if JSON handles this better
print("\nComparison with JSON:")
import json

try:
    large_int = 2**100
    data = {"value": large_int}
    json_str = json.dumps(data)
    print(f"  JSON serialization: SUCCESS")
    print(f"  JSON string length: {len(json_str)} bytes")
    
    # msgpack with same data would fail
    try:
        msgpack_bytes = msgpack_dumps(data)
        print(f"  msgpack bytes length: {len(msgpack_bytes)} bytes")
    except:
        print(f"  msgpack: FAILED as expected")
        
except Exception as e:
    print(f"  JSON FAILED: {e}")

# Check pickle behavior
print("\nComparison with pickle:")
import pickle

try:
    large_int = 2**100
    data = {"value": large_int}
    pickle_bytes = pickle.dumps(data)
    print(f"  Pickle serialization: SUCCESS")
    unpickled = pickle.loads(pickle_bytes)
    assert unpickled["value"] == large_int
    print(f"  Pickle round-trip: SUCCESS")
except Exception as e:
    print(f"  Pickle FAILED: {e}")