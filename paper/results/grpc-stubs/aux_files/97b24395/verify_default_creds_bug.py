#!/usr/bin/env python3
"""Verify if the bug also affects default credential creation."""

import sys
venv_path = '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

import grpc
import grpc.experimental
from grpc._simple_stubs import ChannelCache

cache = ChannelCache.get()

# Test with None credentials (should default to SSL)
target = "localhost:50052"
options = ()

print("Testing with channel_credentials=None (defaults to SSL):")

# First call with None credentials
channel1, _ = cache.get_channel(
    target=target,
    options=options,
    channel_credentials=None,  # Will be replaced with grpc.ssl_channel_credentials()
    insecure=False,
    compression=None,
    method="method1",
    _registered_method=False
)

# Second call with None credentials  
channel2, _ = cache.get_channel(
    target=target,
    options=options,
    channel_credentials=None,  # Will be replaced with grpc.ssl_channel_credentials()
    insecure=False,
    compression=None,
    method="method1",
    _registered_method=False
)

print(f"Channels are same object: {channel1 is channel2}")
print(f"Cache size: {cache._test_only_channel_count()}")

# The bug is in line 186-187 of _simple_stubs.py:
# elif channel_credentials is None:
#     _LOGGER.debug("Defaulting to SSL channel credentials.")
#     channel_credentials = grpc.ssl_channel_credentials()
# 
# This creates a NEW credential object each time, making the cache key different!