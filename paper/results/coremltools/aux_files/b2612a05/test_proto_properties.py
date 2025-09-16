#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.Model_pb2 as Model
import coremltools.proto.DataStructures_pb2 as DS

# Create instances and test basic properties
print("Testing basic protobuf properties:")
print("="*50)

# Test DoubleVector
vec = DS.DoubleVector()
print(f"Empty DoubleVector values: {list(vec.values)}")
vec.values.append(1.0)
vec.values.append(2.0)
print(f"After appending: {list(vec.values)}")
print(f"Can serialize: {vec.SerializeToString()}")

# Test round-trip
serialized = vec.SerializeToString()
vec2 = DS.DoubleVector()
vec2.ParseFromString(serialized)
print(f"Round-trip preserved values: {list(vec2.values) == list(vec.values)}")

print("\n" + "="*50)
print("Testing Int64Vector:")
ivec = DS.Int64Vector()
ivec.values.extend([1, 2, 3, 4, 5])
print(f"Values: {list(ivec.values)}")

# Test serialization
serialized = ivec.SerializeToString()
ivec2 = DS.Int64Vector()
ivec2.ParseFromString(serialized)
print(f"Round-trip preserved: {list(ivec2.values) == list(ivec.values)}")

print("\n" + "="*50)
print("Testing StringVector:")
svec = DS.StringVector()
svec.values.extend(["hello", "world", "🦄"])
print(f"Values: {list(svec.values)}")
serialized = svec.SerializeToString()
svec2 = DS.StringVector()
svec2.ParseFromString(serialized)
print(f"Round-trip preserved: {list(svec2.values) == list(svec.values)}")

print("\n" + "="*50)
print("Testing StringToDoubleMap:")
m = DS.StringToDoubleMap()
m.map["key1"] = 1.5
m.map["key2"] = 2.5
print(f"Map: {dict(m.map)}")
serialized = m.SerializeToString()
m2 = DS.StringToDoubleMap()
m2.ParseFromString(serialized)
print(f"Round-trip preserved: {dict(m2.map) == dict(m.map)}")