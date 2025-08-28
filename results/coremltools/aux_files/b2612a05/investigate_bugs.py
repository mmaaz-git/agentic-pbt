#!/usr/bin/env python3
"""Investigate the bugs found in protobuf property tests."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.DataStructures_pb2 as DS

print("Bug 1: FloatVector precision issue")
print("="*60)

# Test with the failing value
value = 6.407422478066779e-148
vec = DS.FloatVector()
vec.vector.append(value)

print(f"Original value: {value}")
print(f"Stored in vector: {vec.vector[0]}")

# Serialize and deserialize
serialized = vec.SerializeToString()
vec2 = DS.FloatVector()
vec2.ParseFromString(serialized)

print(f"After round-trip: {vec2.vector[0]}")
print(f"Value lost: {vec2.vector[0] == 0.0}")

# Test with numpy to understand float32 behavior
import struct
# Convert to float32 and back
float32_bytes = struct.pack('f', value)
float32_value = struct.unpack('f', float32_bytes)[0]
print(f"As float32: {float32_value}")
print(f"Is denormalized: {value < 1.175494e-38}")  # Minimum normal float32

print("\n" + "="*60)
print("Bug 2: Map serialization order issue")
print("="*60)

# Test the failing case
mapping = {'2': 0, '4': 0, '00000': 0, '00000000000000': 0}

msg1 = DS.StringToInt64Map()
for k, v in mapping.items():
    msg1.map[k] = v

msg2 = DS.StringToInt64Map()
msg2.CopyFrom(msg1)

print(f"Original map: {dict(msg1.map)}")
print(f"Copied map: {dict(msg2.map)}")
print(f"Maps equal: {dict(msg1.map) == dict(msg2.map)}")

ser1 = msg1.SerializeToString()
ser2 = msg2.SerializeToString()

print(f"Serialized bytes equal: {ser1 == ser2}")
print(f"Serialized length msg1: {len(ser1)}")
print(f"Serialized length msg2: {len(ser2)}")

# Check if order matters
print("\nTesting if insertion order affects serialization:")
msg3 = DS.StringToInt64Map()
msg3.map['00000'] = 0
msg3.map['2'] = 0
msg3.map['4'] = 0
msg3.map['00000000000000'] = 0

msg4 = DS.StringToInt64Map()
msg4.map['2'] = 0
msg4.map['4'] = 0
msg4.map['00000'] = 0
msg4.map['00000000000000'] = 0

ser3 = msg3.SerializeToString()
ser4 = msg4.SerializeToString()

print(f"Different insertion order gives same serialization: {ser3 == ser4}")

# Investigate the actual difference
print("\nComparing serializations byte by byte:")
for i, (b1, b2) in enumerate(zip(ser1, ser2)):
    if b1 != b2:
        print(f"Difference at byte {i}: {b1:02x} vs {b2:02x}")
        break