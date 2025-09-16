#!/usr/bin/env python3
"""Minimal reproduction of the CopyFrom serialization order bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.DataStructures_pb2 as DS

# Minimal case that reproduces the bug
mapping = {'000': 0, '001': 0, '0000': 0}

msg1 = DS.StringToInt64Map()
for k, v in mapping.items():
    msg1.map[k] = v

msg2 = DS.StringToInt64Map()
msg2.CopyFrom(msg1)

# The maps are equal
print(f"Maps equal: {dict(msg1.map) == dict(msg2.map)}")
print(f"msg1: {dict(msg1.map)}")
print(f"msg2: {dict(msg2.map)}")

# But serializations differ
ser1 = msg1.SerializeToString()
ser2 = msg2.SerializeToString()

print(f"\nSerializations equal: {ser1 == ser2}")
if ser1 != ser2:
    print(f"msg1 serialized: {ser1.hex()}")
    print(f"msg2 serialized: {ser2.hex()}")
    
    # Parse both serializations back to verify they represent the same data
    msg3 = DS.StringToInt64Map()
    msg3.ParseFromString(ser1)
    msg4 = DS.StringToInt64Map()
    msg4.ParseFromString(ser2)
    print(f"\nBoth deserialize to same map: {dict(msg3.map) == dict(msg4.map)}")