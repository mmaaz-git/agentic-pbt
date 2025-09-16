#!/usr/bin/env /root/hypothesis-llm/envs/grpc-stubs_env/bin/python3

import sys
import os
import threading
import time
import datetime
from unittest import mock

# Add the grpc module path
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

import grpc
from hypothesis import given, strategies as st, settings, assume
import pytest

# Install hypothesis if not available
try:
    import hypothesis
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "hypothesis", "pytest"])
    import hypothesis

# Strategy for generating valid server targets
target_strategy = st.text(min_size=1, max_size=100).filter(lambda x: ':' not in x or x.count(':') == 1)

# Strategy for generating channel options
option_strategy = st.tuples(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50)
)
options_strategy = st.lists(option_strategy, min_size=0, max_size=5)

# Strategy for compression options
compression_strategy = st.sampled_from([None, grpc.Compression.NoCompression, grpc.Compression.Gzip, grpc.Compression.Deflate])

# Property 1: ChannelCache should be a singleton
@given(st.integers(min_value=1, max_value=10))
def test_channel_cache_singleton(n_calls):
    """Test that ChannelCache.get() always returns the same instance."""
    from grpc import _simple_stubs
    instances = []
    for _ in range(n_calls):
        instance = _simple_stubs.ChannelCache.get()
        instances.append(instance)
    
    # All instances should be the same object
    first_instance = instances[0]
    for instance in instances:
        assert instance is first_instance, "ChannelCache.get() should return the same singleton instance"


# Property 2: Mutual exclusivity of insecure and channel_credentials
@given(
    target=target_strategy,
    options=options_strategy,
    channel_credentials=st.one_of(
        st.none(),
        st.just(grpc.ssl_channel_credentials())
    ),
    insecure=st.booleans(),
    compression=compression_strategy,
    method=st.text(min_size=1, max_size=50),
    registered_method=st.booleans()
)
def test_insecure_channel_credentials_mutual_exclusivity(
    target, options, channel_credentials, insecure, compression, method, registered_method
):
    """Test that insecure=True and channel_credentials are mutually exclusive."""
    from grpc import _simple_stubs
    cache = _simple_stubs.ChannelCache.get()
    
    if insecure and channel_credentials is not None:
        # This should raise ValueError
        with pytest.raises(ValueError, match="mutually exclusive"):
            cache.get_channel(
                target, tuple(options), channel_credentials, 
                insecure, compression, method, registered_method
            )
    else:
        # This should not raise an error, but we need to mock channel creation
        with mock.patch.object(_simple_stubs, '_create_channel') as mock_create:
            mock_channel = mock.MagicMock()
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_create.return_value = mock_channel
            
            try:
                channel, handle = cache.get_channel(
                    target, tuple(options), channel_credentials,
                    insecure, compression, method, registered_method
                )
                assert channel is not None
            except Exception as e:
                # Only accept exceptions that are not about mutual exclusivity
                assert "mutually exclusive" not in str(e)


# Property 3: Channel eviction when exceeding maximum channels
@given(
    n_channels=st.integers(min_value=1, max_value=10),
    max_channels=st.integers(min_value=1, max_value=5)
)
@settings(deadline=None)  # Disable deadline for this test due to threading
def test_channel_eviction_max_channels(n_channels, max_channels):
    """Test that channels are evicted when exceeding the maximum."""
    from grpc import _simple_stubs
    # Create a new ChannelCache instance with a controlled maximum
    with mock.patch.object(_simple_stubs, '_MAXIMUM_CHANNELS', max_channels):
        # Clear the singleton
        _simple_stubs.ChannelCache._singleton = None
        cache = _simple_stubs.ChannelCache.get()
        
        # Mock channel creation
        with mock.patch.object(_simple_stubs, '_create_channel') as mock_create:
            channels_created = []
            
            def create_mock_channel(*args, **kwargs):
                mock_channel = mock.MagicMock()
                mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
                mock_channel.close = mock.MagicMock()
                channels_created.append(mock_channel)
                return mock_channel
            
            mock_create.side_effect = create_mock_channel
            
            # Create n_channels with different targets
            for i in range(n_channels):
                target = f"server_{i}:50051"
                cache.get_channel(
                    target, (), None, False, None, "method", False
                )
            
            # Wait a bit for eviction thread to process
            time.sleep(0.1)
            
            # Check that we never exceed max_channels
            current_count = cache._test_only_channel_count()
            assert current_count <= max_channels, f"Channel count {current_count} exceeds maximum {max_channels}"
            
            # If we created more than max, some should have been evicted (closed)
            if n_channels > max_channels:
                closed_count = sum(1 for ch in channels_created if ch.close.called)
                assert closed_count > 0, "Some channels should have been evicted"


# Property 4: Cache key consistency
@given(
    target1=target_strategy,
    target2=target_strategy,
    options1=options_strategy,
    options2=options_strategy,
    compression1=compression_strategy,
    compression2=compression_strategy
)
def test_cache_key_consistency(target1, target2, options1, options2, compression1, compression2):
    """Test that identical parameters result in the same channel, different parameters result in different channels."""
    from grpc import _simple_stubs
    cache = _simple_stubs.ChannelCache.get()
    
    with mock.patch.object(_simple_stubs, '_create_channel') as mock_create:
        channels = {}
        channel_counter = [0]
        
        def create_unique_channel(*args, **kwargs):
            mock_channel = mock.MagicMock()
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_channel.id = channel_counter[0]
            channel_counter[0] += 1
            channels[mock_channel.id] = mock_channel
            return mock_channel
        
        mock_create.side_effect = create_unique_channel
        
        # Get channel with first set of parameters
        channel1, _ = cache.get_channel(
            target1, tuple(options1), None, True, compression1, "method1", False
        )
        
        # Get channel with same parameters - should return same channel
        channel1_again, _ = cache.get_channel(
            target1, tuple(options1), None, True, compression1, "method1", False
        )
        
        assert channel1.id == channel1_again.id, "Same parameters should return the same channel"
        
        # Get channel with different parameters
        channel2, _ = cache.get_channel(
            target2, tuple(options2), None, True, compression2, "method2", False
        )
        
        # Check if parameters are actually different
        params1 = (target1, tuple(options1), compression1)
        params2 = (target2, tuple(options2), compression2)
        
        if params1 != params2:
            assert channel1.id != channel2.id, "Different parameters should return different channels"
        else:
            assert channel1.id == channel2.id, "Same effective parameters should return the same channel"


# Property 5: Thread safety of ChannelCache
@given(
    n_threads=st.integers(min_value=2, max_value=10),
    n_operations=st.integers(min_value=5, max_value=20)
)
@settings(deadline=None)  # Disable deadline for threading test
def test_channel_cache_thread_safety(n_threads, n_operations):
    """Test that ChannelCache operations are thread-safe."""
    from grpc import _simple_stubs
    cache = _simple_stubs.ChannelCache.get()
    errors = []
    
    with mock.patch.object(_simple_stubs, '_create_channel') as mock_create:
        def create_mock_channel(*args, **kwargs):
            mock_channel = mock.MagicMock()
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            return mock_channel
        
        mock_create.side_effect = create_mock_channel
        
        def worker(worker_id):
            try:
                for i in range(n_operations):
                    target = f"server_{worker_id}_{i}:50051"
                    cache.get_channel(
                        target, (), None, True, None, f"method_{i}", False
                    )
            except Exception as e:
                errors.append((worker_id, e))
        
        threads = []
        for i in range(n_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No errors should have occurred
        assert len(errors) == 0, f"Thread safety violations: {errors}"


# Property 6: Default timeout behavior
@given(
    timeout=st.one_of(
        st.none(),
        st.floats(min_value=0.1, max_value=300.0)
    )
)
def test_default_timeout_behavior(timeout):
    """Test that timeout parameter is handled correctly."""
    from grpc import _simple_stubs
    with mock.patch.object(_simple_stubs.ChannelCache, 'get') as mock_cache_get:
        mock_cache = mock.MagicMock()
        mock_channel = mock.MagicMock()
        mock_multicallable = mock.MagicMock()
        mock_channel.unary_unary.return_value = mock_multicallable
        mock_cache.get_channel.return_value = (mock_channel, None)
        mock_cache_get.return_value = mock_cache
        
        # Call unary_unary with or without timeout
        request = "test_request"
        if timeout is not None:
            _simple_stubs.unary_unary(
                request, "localhost:50051", "/test/method",
                timeout=timeout
            )
            # Check that the timeout was passed correctly
            mock_multicallable.assert_called_once()
            call_kwargs = mock_multicallable.call_args[1]
            assert call_kwargs['timeout'] == timeout
        else:
            _simple_stubs.unary_unary(
                request, "localhost:50051", "/test/method",
                timeout=None
            )
            # Check that None timeout was passed
            mock_multicallable.assert_called_once()
            call_kwargs = mock_multicallable.call_args[1]
            assert call_kwargs['timeout'] is None


if __name__ == "__main__":
    print("Running property-based tests for grpc._simple_stubs module...")
    pytest.main([__file__, "-v", "--tb=short"])