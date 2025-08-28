#!/usr/bin/env python3
"""Test to understand protobuf extension number specifications."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from grpc_reflection.v1alpha import reflection_pb2

# Check the field descriptor
import google.protobuf.descriptor as descriptor

# Get the descriptor for ExtensionRequest
ext_req_desc = reflection_pb2.ExtensionRequest.DESCRIPTOR

# Find the extension_number field
for field in ext_req_desc.fields:
    if field.name == "extension_number":
        print(f"Field name: {field.name}")
        print(f"Field type: {field.type}")
        print(f"Field cpp_type: {field.cpp_type}")
        print(f"Field number: {field.number}")
        
        # Check the type
        if field.type == descriptor.FieldDescriptor.TYPE_INT32:
            print("Field is TYPE_INT32 - should be bounded to [-2147483648, 2147483647]")
        elif field.type == descriptor.FieldDescriptor.TYPE_INT64:
            print("Field is TYPE_INT64 - should support larger values")
        
        print(f"\nProtobuf extension numbers are defined to be in range [1, 536870911]")
        print(f"with [19000, 19999] reserved for protobuf implementation")
        
# Test the actual valid range for protobuf extension numbers
print("\n" + "="*60)
print("Testing actual protobuf extension number range:")

test_values = [
    0,
    1,  # Min valid extension
    19000,  # Start of reserved range
    19999,  # End of reserved range  
    536870911,  # Max valid extension (2^29 - 1)
    536870912,  # Just beyond max
]

for val in test_values:
    try:
        req = reflection_pb2.ExtensionRequest(
            containing_type="test.Type",
            extension_number=val
        )
        print(f"✓ {val:10} - accepted")
    except ValueError as e:
        print(f"✗ {val:10} - rejected: {e}")