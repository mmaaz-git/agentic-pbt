#!/usr/bin/env python3
"""Check grpc.experimental for channelz functionality."""

import sys
import os
import inspect

# Add the virtual environment to path
venv_path = '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

import grpc.experimental

print("=== grpc.experimental Module ===")
members = dir(grpc.experimental)
print(f"Members: {members}")

# Check for channelz
channelz_related = [m for m in members if 'channelz' in m.lower()]
if channelz_related:
    print(f"\nChannelz-related: {channelz_related}")
    
# Try to import channelz
try:
    from grpc_channelz.v1 import channelz
    print("\ngrpc_channelz.v1.channelz imported successfully!")
    print(f"channelz members: {dir(channelz)[:20]}")  # First 20 members
except ImportError as e:
    print(f"\nCannot import grpc_channelz.v1.channelz: {e}")

# Check _simple_stubs which might have stub functionality
try:
    import grpc._simple_stubs
    print("\n=== grpc._simple_stubs ===")
    print(f"Location: {grpc._simple_stubs.__file__}")
    stub_members = [m for m in dir(grpc._simple_stubs) if not m.startswith('_')]
    print(f"Public members: {stub_members[:10]}")
except Exception as e:
    print(f"Error exploring _simple_stubs: {e}")