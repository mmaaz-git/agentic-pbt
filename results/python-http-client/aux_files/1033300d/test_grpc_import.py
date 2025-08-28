#!/usr/bin/env python3
"""Test if grpc packages are available."""

import sys
import os

# Add the virtual environment to path
venv_path = '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

try:
    import grpc
    print("grpc module found")
    print(f"grpc version: {grpc.__version__ if hasattr(grpc, '__version__') else 'unknown'}")
    print(f"grpc location: {grpc.__file__}")
except ImportError as e:
    print(f"grpc module not found: {e}")

try:
    from grpc import channelz
    print("grpc.channelz module found")
    print(f"channelz location: {channelz.__file__ if hasattr(channelz, '__file__') else 'module location unknown'}")
except ImportError as e:
    print(f"grpc.channelz module not found: {e}")
    
try:
    import grpc_channelz
    print("grpc_channelz module found")
except ImportError as e:
    print(f"grpc_channelz module not found: {e}")