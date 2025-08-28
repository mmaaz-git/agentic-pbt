#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.DataStructures_pb2 as DS

# Inspect DoubleVector structure
vec = DS.DoubleVector()
print("DoubleVector attributes:")
print("="*50)

# Get all non-private attributes
attrs = [a for a in dir(vec) if not a.startswith('_')]
for attr in attrs:
    try:
        val = getattr(vec, attr)
        if not callable(val):
            print(f"  {attr}: {type(val).__name__}")
    except:
        pass

print("\n" + "="*50)
print("HasField method check:")
# Check if it has a HasField method
if hasattr(vec, 'HasField'):
    print("  HasField exists")
    
print("\n" + "="*50)
print("DESCRIPTOR fields:")
if hasattr(vec, 'DESCRIPTOR'):
    desc = vec.DESCRIPTOR
    if hasattr(desc, 'fields'):
        for field in desc.fields:
            print(f"  Field: {field.name} (type: {field.type})")
    
print("\n" + "="*50)
print("Testing actual usage:")
# Try to set and get values
vec.vector.extend([1.0, 2.0, 3.0])
print(f"After extending vector: {list(vec.vector)}")
serialized = vec.SerializeToString()
print(f"Serialized: {serialized}")
vec2 = DS.DoubleVector()
vec2.ParseFromString(serialized)
print(f"Deserialized: {list(vec2.vector)}")