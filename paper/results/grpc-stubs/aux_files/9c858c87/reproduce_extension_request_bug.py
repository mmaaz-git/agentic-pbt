#!/usr/bin/env python3
"""Minimal reproduction of ExtensionRequest integer overflow bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from grpc_reflection.v1alpha import reflection_pb2

# Test valid int32 boundaries
print("Testing int32 boundaries...")

# Max int32
try:
    request = reflection_pb2.ExtensionRequest(
        containing_type="test.Type",
        extension_number=2147483647  # Max int32
    )
    print(f"✓ Max int32 (2147483647) works: {request.extension_number}")
except ValueError as e:
    print(f"✗ Max int32 failed: {e}")

# Max int32 + 1
try:
    request = reflection_pb2.ExtensionRequest(
        containing_type="test.Type",
        extension_number=2147483648  # Max int32 + 1
    )
    print(f"✓ Max int32 + 1 (2147483648) works: {request.extension_number}")
except ValueError as e:
    print(f"✗ Max int32 + 1 (2147483648) failed: {e}")

# Min int32
try:
    request = reflection_pb2.ExtensionRequest(
        containing_type="test.Type",
        extension_number=-2147483648  # Min int32
    )
    print(f"✓ Min int32 (-2147483648) works: {request.extension_number}")
except ValueError as e:
    print(f"✗ Min int32 failed: {e}")

# Min int32 - 1
try:
    request = reflection_pb2.ExtensionRequest(
        containing_type="test.Type",
        extension_number=-2147483649  # Min int32 - 1
    )
    print(f"✓ Min int32 - 1 (-2147483649) works: {request.extension_number}")
except ValueError as e:
    print(f"✗ Min int32 - 1 (-2147483649) failed: {e}")

print("\nConclusion: ExtensionRequest.extension_number field has int32 bounds")
print("but raises ValueError instead of truncating or handling gracefully.")