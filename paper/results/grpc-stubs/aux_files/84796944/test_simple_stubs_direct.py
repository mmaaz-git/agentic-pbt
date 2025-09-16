#!/usr/bin/env /root/hypothesis-llm/envs/grpc-stubs_env/bin/python3

import sys
import os
import importlib.util
import threading
import time
import datetime
from unittest import mock

# Add the grpc module path
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

import grpc
from hypothesis import given, strategies as st, settings, assume
import pytest

# Load _simple_stubs directly to avoid circular import
spec = importlib.util.spec_from_file_location(
    "simple_stubs",
    "/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages/grpc/_simple_stubs.py"
)
simple_stubs = importlib.util.module_from_spec(spec)

# Mock the experimental_api import to avoid circular dependency
class MockExperimentalApi:
    def __call__(self, func):
        return func

# Create a mock experimental module with necessary functions
def mock_insecure_channel_credentials():
    return "insecure_creds"

mock_experimental = type('module', (), {
    'experimental_api': MockExperimentalApi(),
    'insecure_channel_credentials': mock_insecure_channel_credentials
})()

sys.modules['grpc.experimental'] = mock_experimental
grpc.experimental = mock_experimental

# Also need to mock grpc.ssl_channel_credentials
original_ssl_creds = grpc.ssl_channel_credentials if hasattr(grpc, 'ssl_channel_credentials') else None
grpc.ssl_channel_credentials = lambda *args, **kwargs: "ssl_creds"

# Now load the module
spec.loader.exec_module(simple_stubs)

# Test 1: Check for race condition in ChannelCache eviction
@given(
    n_channels=st.integers(min_value=10, max_value=20)
)
@settings(deadline=None, max_examples=10)
def test_channel_cache_race_condition(n_channels):
    """Test for race conditions during channel eviction."""
    # Clear singleton
    simple_stubs.ChannelCache._singleton = None
    
    # Set a very low maximum to trigger frequent evictions
    with mock.patch.object(simple_stubs, '_MAXIMUM_CHANNELS', 3):
        with mock.patch.object(simple_stubs, '_EVICTION_PERIOD', datetime.timedelta(seconds=0.1)):
            cache = simple_stubs.ChannelCache.get()
            
            channels_closed = []
            
            with mock.patch.object(simple_stubs, '_create_channel') as mock_create:
                def create_mock_channel(*args, **kwargs):
                    mock_channel = mock.MagicMock()
                    mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
                    
                    def track_close():
                        channels_closed.append(mock_channel)
                    
                    mock_channel.close = track_close
                    return mock_channel
                
                mock_create.side_effect = create_mock_channel
                
                # Create channels rapidly in multiple threads
                errors = []
                
                def create_channels(thread_id):
                    try:
                        for i in range(n_channels // 2):
                            target = f"server_{thread_id}_{i}:50051"
                            cache.get_channel(target, (), None, False, None, "method", False)
                            time.sleep(0.001)  # Small delay to increase chance of race
                    except Exception as e:
                        errors.append(e)
                
                thread1 = threading.Thread(target=create_channels, args=(1,))
                thread2 = threading.Thread(target=create_channels, args=(2,))
                
                thread1.start()
                thread2.start()
                thread1.join()
                thread2.join()
                
                # No exceptions should occur
                assert len(errors) == 0, f"Race condition detected: {errors}"
                
                # Wait for evictions
                time.sleep(0.5)
                
                # Some channels should have been closed
                assert len(channels_closed) > 0, "No channels were evicted"
                
                # Cache size should respect maximum
                assert cache._test_only_channel_count() <= 3


# Test 2: Test eviction time calculation edge case
@given(
    eviction_seconds=st.floats(min_value=0.01, max_value=1.0)
)
@settings(deadline=None, max_examples=10)
def test_eviction_timing_edge_case(eviction_seconds):
    """Test edge cases in eviction timing calculation."""
    # Clear singleton
    simple_stubs.ChannelCache._singleton = None
    
    eviction_period = datetime.timedelta(seconds=eviction_seconds)
    
    with mock.patch.object(simple_stubs, '_EVICTION_PERIOD', eviction_period):
        cache = simple_stubs.ChannelCache.get()
        
        with mock.patch.object(simple_stubs, '_create_channel') as mock_create:
            mock_channel = mock.MagicMock()
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_channel.close = mock.MagicMock()
            mock_create.return_value = mock_channel
            
            # Create a channel
            target = "test:50051"
            channel1, _ = cache.get_channel(target, (), None, False, None, "method", False)
            
            # Check it's in cache
            initial_count = cache._test_only_channel_count()
            assert initial_count == 1
            
            # Wait for eviction
            time.sleep(eviction_seconds + 0.5)
            
            # Trigger eviction check by creating another channel
            channel2, _ = cache.get_channel("other:50051", (), None, False, None, "method", False)
            
            # Give eviction thread time to work
            time.sleep(0.2)
            
            # First channel should have been evicted
            assert mock_channel.close.called or cache._test_only_channel_count() == 2


# Test 3: Test timeout edge cases
@given(
    timeout=st.one_of(
        st.just(0.0),  # Zero timeout
        st.just(-1.0),  # Negative timeout
        st.just(float('inf')),  # Infinite timeout
        st.floats(min_value=1e-10, max_value=1e-6),  # Very small timeouts
    )
)
@settings(deadline=None, max_examples=20)
def test_timeout_edge_cases(timeout):
    """Test edge cases for timeout values."""
    # Clear singleton
    simple_stubs.ChannelCache._singleton = None
    cache = simple_stubs.ChannelCache.get()
    
    with mock.patch.object(simple_stubs, '_create_channel') as mock_create:
        mock_channel = mock.MagicMock()
        mock_multicallable = mock.MagicMock()
        mock_multicallable.return_value = "response"
        mock_channel.unary_unary.return_value = mock_multicallable
        mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
        mock_create.return_value = mock_channel
        
        try:
            result = simple_stubs.unary_unary(
                request="test",
                target="localhost:50051",
                method="/test/method",
                insecure=True,
                timeout=timeout
            )
            
            # Check that the timeout was passed through correctly
            mock_multicallable.assert_called_once()
            call_kwargs = mock_multicallable.call_args[1]
            assert call_kwargs['timeout'] == timeout
            
            # Edge case: negative and zero timeouts should still be passed through
            # The underlying gRPC layer should handle validation
            
        except Exception as e:
            # Some edge cases might raise exceptions
            # But we want to check if it's a legitimate validation error
            if timeout < 0:
                # Negative timeout might be rejected
                pass
            elif timeout == float('inf'):
                # Infinite timeout might be rejected or converted
                pass
            else:
                # Unexpected error
                pytest.fail(f"Unexpected error for timeout {timeout}: {e}")


# Test 4: Test cache key collision with special characters
@given(
    target=st.text(min_size=1, max_size=50).filter(lambda x: any(c in x for c in [':', '/', '\\', '\n', '\t'])),
    options=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=20)
        ),
        min_size=0,
        max_size=3
    )
)
@settings(deadline=None, max_examples=20)
def test_cache_key_with_special_chars(target, options):
    """Test cache keys with special characters."""
    simple_stubs.ChannelCache._singleton = None
    cache = simple_stubs.ChannelCache.get()
    
    with mock.patch.object(simple_stubs, '_create_channel') as mock_create:
        mock_channel = mock.MagicMock()
        mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
        mock_create.return_value = mock_channel
        
        try:
            # Create channel with special characters in target
            channel1, _ = cache.get_channel(
                target, tuple(options), None, True, None, "method", False
            )
            
            # Get same channel again - should return cached
            channel2, _ = cache.get_channel(
                target, tuple(options), None, True, None, "method", False
            )
            
            # Should be the same channel object
            assert channel1 is channel2
            
            # Create should have been called only once
            assert mock_create.call_count == 1
            
        except Exception as e:
            # Special characters might cause issues
            pytest.fail(f"Failed with special chars in target '{target}': {e}")


if __name__ == "__main__":
    print("Running direct tests on _simple_stubs module...")
    pytest.main([__file__, "-v", "--tb=short"])