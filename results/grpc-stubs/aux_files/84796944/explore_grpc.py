#!/usr/bin/env /root/hypothesis-llm/envs/grpc-stubs_env/bin/python3

import grpc
import grpc_tools
import inspect
import sys

print("gRPC version:", grpc.__version__)
print("\nAvailable modules in grpc:")
grpc_members = [name for name in dir(grpc) if not name.startswith('_')]
print(grpc_members[:20])  # First 20 members

print("\n\nChecking for stub-related classes and functions:")
stub_related = [name for name in dir(grpc) if 'stub' in name.lower()]
print("Stub-related items:", stub_related)

# Check if there's a stub module
try:
    import grpc.framework.interfaces.face.face as face
    print("\nFound grpc.framework.interfaces.face")
except ImportError:
    pass

# Check for channel and stub functionality
print("\n\nChannel classes:")
channel_classes = [name for name in dir(grpc) if 'Channel' in name]
print(channel_classes)

print("\n\nChecking grpc_tools:")
tools_members = [name for name in dir(grpc_tools) if not name.startswith('_')]
print("grpc_tools members:", tools_members[:20])