#!/usr/bin/env python3
"""Property-based tests for grpc._simple_stubs module using Hypothesis."""

import sys
import os
import threading
import time
from unittest import mock

# Add the virtual environment to path
venv_path = '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

import grpc
import grpc.experimental  # Import experimental first to avoid circular import
from grpc.experimental import unary_unary  # Import the functions we need
from grpc._simple_stubs import ChannelCache  # Import ChannelCache directly
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test 1: Singleton invariant - ChannelCache.get() always returns the same instance
@given(st.integers(min_value=1, max_value=10))
def test_channel_cache_singleton_invariant(num_calls):
    """Test that ChannelCache.get() always returns the same singleton instance."""
    instances = []
    for _ in range(num_calls):
        instance = ChannelCache.get()
        instances.append(instance)
    
    # All instances should be the same object
    first_instance = instances[0]
    for instance in instances:
        assert instance is first_instance, "ChannelCache.get() returned different instances"


# Test 2: Mutual exclusivity of insecure and channel_credentials
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: ':' in x),  # target with port
    st.text(min_size=1, max_size=100),  # method name
    st.booleans(),  # insecure flag
    st.booleans(),  # whether to provide channel_credentials
)
def test_mutual_exclusivity_insecure_channel_credentials(target, method, insecure, has_credentials):
    """Test that insecure=True and channel_credentials are mutually exclusive."""
    
    # Only test the invalid combination
    if not (insecure and has_credentials):
        return  # Skip valid combinations
    
    # Create mock credentials
    channel_credentials = mock.MagicMock(spec=grpc.ChannelCredentials)
    
    # Create a simple request object
    request = b"test_request"
    
    # This should raise ValueError according to the documented behavior
    with pytest.raises(ValueError) as exc_info:
        unary_unary(
            request=request,
            target=target,
            method=method,
            insecure=insecure,
            channel_credentials=channel_credentials if has_credentials else None,
            timeout=0.1  # Short timeout to avoid hanging
        )
    
    assert "mutually exclusive" in str(exc_info.value).lower()


# Test 3: Channel reuse property - same parameters should reuse the same channel
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: ':' in x),  # target
    st.text(min_size=1, max_size=50),  # method
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=20)
        ),
        max_size=3
    ),  # options
    st.booleans(),  # insecure
    st.sampled_from([None, grpc.Compression.NoCompression, grpc.Compression.Gzip]),  # compression
)
@settings(deadline=1000)  # Allow more time for this test
def test_channel_reuse_property(target, method, options, insecure, compression):
    """Test that the same parameters result in channel reuse from the cache."""
    
    cache = ChannelCache.get()
    
    # Convert options to the expected format
    options_tuple = tuple(options)
    
    # Make the first call to populate the cache
    channel1, handle1 = cache.get_channel(
        target=target,
        options=options_tuple,
        channel_credentials=None if insecure else grpc.ssl_channel_credentials(),
        insecure=insecure,
        compression=compression,
        method=method,
        _registered_method=False
    )
    
    # Make the second call with identical parameters
    channel2, handle2 = cache.get_channel(
        target=target,
        options=options_tuple,
        channel_credentials=None if insecure else grpc.ssl_channel_credentials(),
        insecure=insecure,
        compression=compression,
        method=method,
        _registered_method=False
    )
    
    # Channels should be the same object (reused from cache)
    assert channel1 is channel2, "Same parameters did not reuse the cached channel"


# Test 4: Cache size limit property
@given(
    st.integers(min_value=1, max_value=10),  # number of unique channels to create
    st.integers(min_value=1, max_value=5),  # max channels limit to set
)
@settings(deadline=2000)
def test_cache_size_limit(num_channels, max_channels):
    """Test that the cache respects the maximum channel limit."""
    
    # Mock the environment variable for maximum channels
    with mock.patch.dict(os.environ, {'GRPC_PYTHON_MANAGED_CHANNEL_MAXIMUM': str(max_channels)}):
        # We need to reset the singleton to pick up the new environment variable
        with mock.patch.object(ChannelCache, '_singleton', None):
            with mock.patch.object(ChannelCache, '_MAXIMUM_CHANNELS', max_channels):
                cache = ChannelCache.get()
                
                # Create more channels than the maximum
                channels = []
                for i in range(num_channels):
                    target = f"localhost:{9000 + i}"
                    channel, _ = cache.get_channel(
                        target=target,
                        options=(),
                        channel_credentials=grpc.ssl_channel_credentials(),
                        insecure=False,
                        compression=None,
                        method="test_method",
                        _registered_method=False
                    )
                    channels.append(channel)
                    
                    # Give the eviction thread time to work
                    time.sleep(0.01)
                
                # The cache should never exceed the maximum
                channel_count = cache._test_only_channel_count()
                assert channel_count <= max_channels, f"Cache size {channel_count} exceeds maximum {max_channels}"


# Test 5: Default timeout property
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: ':' in x),  # target
    st.text(min_size=1, max_size=50),  # method
    st.one_of(st.none(), st.floats(min_value=0.1, max_value=120.0)),  # timeout
)
def test_default_timeout_property(target, method, timeout):
    """Test that the timeout defaults to the expected value when not specified."""
    
    # Create a mock channel that captures the timeout
    captured_timeout = None
    
    def mock_unary_unary(method, request_serializer, response_deserializer, method_handle):
        def multicallable(request, metadata=None, wait_for_ready=None, credentials=None, timeout=None):
            nonlocal captured_timeout
            captured_timeout = timeout
            return mock.MagicMock()  # Return a mock response
        return multicallable
    
    with mock.patch('grpc.secure_channel') as mock_secure_channel:
        mock_channel = mock.MagicMock()
        mock_channel.unary_unary = mock_unary_unary
        mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
        mock_secure_channel.return_value = mock_channel
        
        # Call unary_unary with or without timeout
        try:
            unary_unary(
                request=b"test",
                target=target,
                method=method,
                timeout=timeout,
                insecure=True
            )
        except Exception:
            pass  # We're only interested in the timeout value
        
        # Check the captured timeout
        if timeout is None:
            # Should use the default timeout (60.0 seconds)
            assert captured_timeout == 60.0, f"Expected default timeout 60.0, got {captured_timeout}"
        else:
            assert captured_timeout == timeout, f"Expected timeout {timeout}, got {captured_timeout}"


# Test 6: Thread safety of ChannelCache
@given(
    st.integers(min_value=2, max_value=5),  # number of threads
    st.integers(min_value=1, max_value=10),  # operations per thread
)
@settings(deadline=3000)
def test_channel_cache_thread_safety(num_threads, ops_per_thread):
    """Test that ChannelCache operations are thread-safe."""
    
    cache = ChannelCache.get()
    errors = []
    
    def worker(thread_id):
        try:
            for i in range(ops_per_thread):
                target = f"localhost:{8000 + thread_id * 100 + i}"
                channel, _ = cache.get_channel(
                    target=target,
                    options=(),
                    channel_credentials=grpc.ssl_channel_credentials(),
                    insecure=False,
                    compression=None,
                    method=f"method_{thread_id}_{i}",
                    _registered_method=False
                )
                # Verify we got a channel
                assert channel is not None
        except Exception as e:
            errors.append(e)
    
    # Start multiple threads
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # No errors should have occurred
    assert len(errors) == 0, f"Thread safety violations: {errors}"