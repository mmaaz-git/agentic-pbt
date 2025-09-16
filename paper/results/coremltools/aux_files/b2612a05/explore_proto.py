#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import inspect
import coremltools.proto as proto

# Get all members of the proto module
members = inspect.getmembers(proto)

print("coremltools.proto module members:")
print("=" * 50)

for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"{name}: {obj_type}")
        
print("\n" + "=" * 50)
print("Protobuf modules available:")
print("=" * 50)

# List the protobuf modules
import os
proto_dir = os.path.dirname(proto.__file__)
pb2_files = [f for f in os.listdir(proto_dir) if f.endswith('_pb2.py')]
for f in sorted(pb2_files):
    print(f)