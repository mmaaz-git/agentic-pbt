#!/usr/bin/env python3
"""Test the specific failing case for CopyFrom."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.DataStructures_pb2 as DS

# Exact failing case from hypothesis
mapping = {'2': 0, '4': 0, '00000': 0, '00000000000000': 0}

print("Testing the exact failing case:")
print("="*60)

msg1 = DS.StringToInt64Map()
for k, v in mapping.items():
    msg1.map[k] = v

msg2 = DS.StringToInt64Map()
msg2.CopyFrom(msg1)

print(f"msg1 map: {dict(msg1.map)}")
print(f"msg2 map: {dict(msg2.map)}")
print(f"Maps equal: {dict(msg1.map) == dict(msg2.map)}")

ser1 = msg1.SerializeToString()
ser2 = msg2.SerializeToString()

print(f"Serialization lengths: {len(ser1)} vs {len(ser2)}")
print(f"Serializations equal: {ser1 == ser2}")

if ser1 != ser2:
    print("\nSerializations differ!")
    print(f"ser1: {ser1.hex()}")
    print(f"ser2: {ser2.hex()}")
    
    # Find differences
    print("\nDifferences:")
    for i, (b1, b2) in enumerate(zip(ser1, ser2)):
        if b1 != b2:
            print(f"  Byte {i}: 0x{b1:02x} vs 0x{b2:02x}")
    
    # Check if lengths differ
    if len(ser1) != len(ser2):
        print(f"Length difference: {len(ser1)} vs {len(ser2)}")

print("\n" + "="*60)
print("Testing with fresh messages multiple times:")

for i in range(5):
    m1 = DS.StringToInt64Map()
    for k, v in mapping.items():
        m1.map[k] = v
    
    m2 = DS.StringToInt64Map()
    m2.CopyFrom(m1)
    
    s1 = m1.SerializeToString()
    s2 = m2.SerializeToString()
    
    print(f"Run {i+1}: {'EQUAL' if s1 == s2 else 'DIFFERENT'}")
    if s1 != s2:
        print(f"  Lengths: {len(s1)} vs {len(s2)}")