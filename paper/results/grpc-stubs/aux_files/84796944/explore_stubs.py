#!/usr/bin/env /root/hypothesis-llm/envs/grpc-stubs_env/bin/python3

import grpc
import inspect
import sys
import os

# Explore grpc module structure
print("=== Exploring gRPC Stub-related Functionality ===\n")

# Get the grpc module file location
print(f"gRPC module location: {grpc.__file__}")
grpc_dir = os.path.dirname(grpc.__file__)
print(f"gRPC directory: {grpc_dir}\n")

# Check for stub-related functionality
print("=== Key gRPC Classes for Stubs ===\n")

# Channel is used to create stubs
if hasattr(grpc, 'Channel'):
    print(f"grpc.Channel: {grpc.Channel}")
    print(f"Channel methods: {[m for m in dir(grpc.Channel) if not m.startswith('_')]}\n")

# Check for stub generation functions
stub_functions = []
for name in dir(grpc):
    obj = getattr(grpc, name)
    if callable(obj) and 'stub' in name.lower():
        stub_functions.append(name)

print(f"Stub-related functions: {stub_functions}\n")

# Check for method types used in stubs
method_types = [name for name in dir(grpc) if 'unary' in name.lower() or 'stream' in name.lower()]
print(f"Method types (for RPC calls): {method_types}\n")

# Check the actual channel methods
if hasattr(grpc, 'insecure_channel'):
    print("grpc.insecure_channel signature:", inspect.signature(grpc.insecure_channel))
if hasattr(grpc, 'secure_channel'):
    print("grpc.secure_channel signature:", inspect.signature(grpc.secure_channel))

print("\n=== Interceptor Classes (often used with stubs) ===\n")
interceptors = [name for name in dir(grpc) if 'interceptor' in name.lower()]
print(f"Interceptor-related: {interceptors}\n")

# Check for any experimental features
try:
    import grpc.experimental
    exp_members = [m for m in dir(grpc.experimental) if not m.startswith('_')]
    print(f"grpc.experimental members: {exp_members[:10]}")
except ImportError:
    print("No grpc.experimental module")

# List Python files in grpc directory to understand structure
print(f"\n=== Python files in gRPC module ===")
py_files = []
for root, dirs, files in os.walk(grpc_dir):
    # Don't go too deep
    if root.count(os.sep) - grpc_dir.count(os.sep) > 2:
        continue
    for file in files:
        if file.endswith('.py') and 'stub' in file.lower():
            rel_path = os.path.relpath(os.path.join(root, file), grpc_dir)
            py_files.append(rel_path)

if py_files:
    print(f"Files with 'stub' in name: {py_files[:10]}")
else:
    print("No files with 'stub' in name found")