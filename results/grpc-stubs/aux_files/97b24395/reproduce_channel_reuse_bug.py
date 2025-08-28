#!/usr/bin/env python3
"""Minimal reproduction of the channel reuse bug in grpc._simple_stubs."""

import sys
venv_path = '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

import grpc
import grpc.experimental  # Import experimental first to avoid circular import
from grpc._simple_stubs import ChannelCache

# Get the cache singleton
cache = ChannelCache.get()

# Same parameters for both calls
target = "localhost:50051"
options = ()
insecure = False
compression = None
method = "test_method"

# Create two credential objects with the same configuration
creds1 = grpc.ssl_channel_credentials()
creds2 = grpc.ssl_channel_credentials()

print(f"Credentials are same object: {creds1 is creds2}")
print(f"Credentials equal: {creds1 == creds2}")

# Get channel with first credentials
channel1, _ = cache.get_channel(
    target=target,
    options=options,
    channel_credentials=creds1,
    insecure=insecure,
    compression=compression,
    method=method,
    _registered_method=False
)

# Get channel with second credentials (same config, different object)
channel2, _ = cache.get_channel(
    target=target,
    options=options,
    channel_credentials=creds2,
    insecure=insecure,
    compression=compression,
    method=method,
    _registered_method=False
)

print(f"Channels are same object (should be True for reuse): {channel1 is channel2}")
print(f"Cache size (should be 1 if reused): {cache._test_only_channel_count()}")

# Demonstrate the issue: cache key uses object identity, not value
key1 = (target, options, creds1, compression)
key2 = (target, options, creds2, compression)
print(f"Cache keys are equal: {key1 == key2}")