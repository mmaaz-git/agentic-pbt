#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.DataStructures_pb2 as DS
import coremltools.proto.Model_pb2 as Model
import coremltools.proto.FeatureTypes_pb2 as FT

print("Exploring key protobuf message types and their properties:")
print("="*60)

# Test various vector types
messages_to_test = [
    (DS.DoubleVector, "DoubleVector", "vector"),
    (DS.FloatVector, "FloatVector", "vector"),
    (DS.Int64Vector, "Int64Vector", "vector"),
    (DS.StringVector, "StringVector", "vector"),
    (DS.StringToDoubleMap, "StringToDoubleMap", "map"),
    (DS.StringToInt64Map, "StringToInt64Map", "map"),
    (DS.Int64ToDoubleMap, "Int64ToDoubleMap", "map"),
    (DS.Int64ToStringMap, "Int64ToStringMap", "map"),
]

for msg_class, name, field_name in messages_to_test:
    print(f"\n{name}:")
    msg = msg_class()
    
    # Check field exists
    if hasattr(msg, field_name):
        field = getattr(msg, field_name)
        print(f"  Field '{field_name}' type: {type(field).__name__}")
        
        # Test basic operations
        if "Vector" in name:
            # Test vector operations
            if "Double" in name:
                field.extend([1.0, 2.0, 3.0])
            elif "Float" in name:
                field.extend([1.0, 2.0, 3.0])
            elif "Int64" in name:
                field.extend([1, 2, 3])
            elif "String" in name:
                field.extend(["a", "b", "c"])
            
            print(f"  After extending: {list(field)}")
            
            # Test serialization round-trip
            serialized = msg.SerializeToString()
            msg2 = msg_class()
            msg2.ParseFromString(serialized)
            field2 = getattr(msg2, field_name)
            print(f"  Round-trip preserved: {list(field) == list(field2)}")
            
        elif "Map" in name:
            # Test map operations
            if name == "StringToDoubleMap":
                field["key1"] = 1.5
                field["key2"] = 2.5
            elif name == "StringToInt64Map":
                field["key1"] = 100
                field["key2"] = 200
            elif name == "Int64ToDoubleMap":
                field[1] = 1.5
                field[2] = 2.5
            elif name == "Int64ToStringMap":
                field[1] = "value1"
                field[2] = "value2"
            
            print(f"  Map size: {len(field)}")
            
            # Test serialization round-trip
            serialized = msg.SerializeToString()
            msg2 = msg_class()
            msg2.ParseFromString(serialized)
            field2 = getattr(msg2, field_name)
            print(f"  Round-trip preserved: {dict(field) == dict(field2)}")

# Test nested messages
print("\n" + "="*60)
print("Testing nested protobuf messages:")

# Test ArrayFeatureType with shape
arr_type = FT.ArrayFeatureType()
arr_type.shape.extend([224, 224, 3])
print(f"ArrayFeatureType shape: {list(arr_type.shape)}")

# Round-trip test
serialized = arr_type.SerializeToString()
arr_type2 = FT.ArrayFeatureType()
arr_type2.ParseFromString(serialized)
print(f"Round-trip preserved shape: {list(arr_type.shape) == list(arr_type2.shape)}")

# Test clearing and re-parsing
arr_type2.Clear()
print(f"After Clear(): {list(arr_type2.shape)}")
arr_type2.ParseFromString(serialized)
print(f"After re-parsing: {list(arr_type2.shape)}")