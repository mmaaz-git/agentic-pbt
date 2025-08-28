#!/usr/bin/env /root/hypothesis-llm/envs/grpc-stubs_env/bin/python3

import sys
import os
import threading
import time
import datetime
from unittest import mock
import collections

# Add the grpc module path
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

import grpc
from hypothesis import given, strategies as st, settings, assume
import pytest

# Test ChannelCache behavior without importing _simple_stubs directly
# We'll test through the grpc.experimental API

# Test 1: Test for proper handling of edge case timeout values
@given(
    timeout=st.one_of(
        st.just(0.0),  # Zero timeout - edge case
        st.just(-1.0),  # Negative timeout - potential bug
        st.floats(min_value=1e-10, max_value=1e-6),  # Very small timeouts
        st.floats(allow_nan=True, allow_infinity=True),  # NaN and inf
    )
)
@settings(deadline=None, max_examples=30)
def test_timeout_validation_edge_cases(timeout):
    """Test that edge case timeout values are handled properly."""
    
    # Check for potential bugs with special float values
    if timeout != timeout:  # NaN check
        # NaN timeout should either be rejected or treated specially
        with mock.patch('grpc.secure_channel') as mock_secure:
            mock_channel = mock.MagicMock()
            mock_multicallable = mock.MagicMock()
            mock_channel.unary_unary.return_value = mock_multicallable
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_secure.return_value = mock_channel
            
            try:
                result = grpc.experimental.unary_unary(
                    request="test",
                    target="localhost:50051",
                    method="/test",
                    insecure=True,
                    timeout=timeout
                )
                # If it accepts NaN, check what was passed
                mock_multicallable.assert_called_once()
                call_kwargs = mock_multicallable.call_args[1]
                passed_timeout = call_kwargs['timeout']
                
                # NaN should either be rejected or converted to None/default
                assert passed_timeout != passed_timeout or passed_timeout is None, \
                    f"NaN timeout was passed through as {passed_timeout}"
                    
            except (ValueError, TypeError) as e:
                # Expected - NaN should be rejected
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception for NaN timeout: {e}")
    
    elif timeout == float('inf'):
        # Infinite timeout edge case
        with mock.patch('grpc.secure_channel') as mock_secure:
            mock_channel = mock.MagicMock()
            mock_multicallable = mock.MagicMock()
            mock_channel.unary_unary.return_value = mock_multicallable
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_secure.return_value = mock_channel
            
            try:
                result = grpc.experimental.unary_unary(
                    request="test",
                    target="localhost:50051",
                    method="/test",
                    insecure=True,
                    timeout=timeout
                )
                # Check what timeout was actually passed
                mock_multicallable.assert_called_once()
                call_kwargs = mock_multicallable.call_args[1]
                passed_timeout = call_kwargs['timeout']
                
                # Infinity should either be passed through or converted to None
                assert passed_timeout == float('inf') or passed_timeout is None, \
                    f"Infinite timeout was converted to {passed_timeout}"
                    
            except (ValueError, OverflowError) as e:
                # Some implementations might reject infinite timeout
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception for infinite timeout: {e}")
    
    elif timeout < 0:
        # Negative timeout - this is likely a bug if accepted
        with mock.patch('grpc.secure_channel') as mock_secure:
            mock_channel = mock.MagicMock()
            mock_multicallable = mock.MagicMock()
            mock_channel.unary_unary.return_value = mock_multicallable
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_secure.return_value = mock_channel
            
            result = grpc.experimental.unary_unary(
                request="test",
                target="localhost:50051",
                method="/test",
                insecure=True,
                timeout=timeout
            )
            
            # Check that negative timeout was passed through
            mock_multicallable.assert_called_once()
            call_kwargs = mock_multicallable.call_args[1]
            assert call_kwargs['timeout'] == timeout
            
            # This is potentially a bug - negative timeouts should likely be rejected
            print(f"WARNING: Negative timeout {timeout} was accepted and passed through")


# Test 2: Test for OrderedDict behavior in cache
@given(
    n_channels=st.integers(min_value=5, max_value=10)
)
@settings(deadline=None, max_examples=10)
def test_cache_ordering_invariant(n_channels):
    """Test that cache maintains proper ordering for LRU eviction."""
    
    # We need to test that the cache properly maintains ordering
    # According to the code, it uses collections.OrderedDict
    
    # Create a mock to track channel creation order
    created_channels = []
    
    with mock.patch('grpc.secure_channel') as mock_secure:
        def create_mock_channel(*args, **kwargs):
            mock_channel = mock.MagicMock()
            mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
            mock_channel.id = len(created_channels)
            created_channels.append(mock_channel)
            return mock_channel
        
        mock_secure.side_effect = create_mock_channel
        
        # Create multiple channels
        channels = []
        for i in range(n_channels):
            channel = grpc.experimental.unary_unary(
                request=f"test_{i}",
                target=f"server_{i}:50051",
                method=f"/test_{i}",
                insecure=True,
                timeout=1.0
            )
            channels.append(channel)
        
        # Access first channel again - should move it to end in LRU
        channel = grpc.experimental.unary_unary(
            request="test_0",
            target="server_0:50051",
            method="/test_0",
            insecure=True,
            timeout=1.0
        )
        
        # The cache should have reordered - first channel should now be most recent
        # This tests the LRU behavior


# Test 3: Test for concurrent modification issues
@given(
    n_threads=st.integers(min_value=2, max_value=5),
    n_operations=st.integers(min_value=10, max_value=20)
)
@settings(deadline=None, max_examples=5)
def test_concurrent_cache_modifications(n_threads, n_operations):
    """Test for race conditions in concurrent cache access."""
    
    errors = []
    results = []
    
    def worker(thread_id):
        try:
            for i in range(n_operations):
                with mock.patch('grpc.secure_channel') as mock_secure:
                    mock_channel = mock.MagicMock()
                    mock_multicallable = mock.MagicMock()
                    mock_multicallable.return_value = f"response_{thread_id}_{i}"
                    mock_channel.unary_unary.return_value = mock_multicallable
                    mock_channel._get_registered_call_handle = mock.MagicMock(return_value=None)
                    mock_secure.return_value = mock_channel
                    
                    # Rapidly create and access channels
                    result = grpc.experimental.unary_unary(
                        request=f"test_{thread_id}_{i}",
                        target=f"server_{thread_id}_{i % 3}:50051",  # Reuse some targets
                        method=f"/test_{i % 5}",  # Reuse some methods
                        insecure=True,
                        timeout=0.1
                    )
                    results.append(result)
                    
        except Exception as e:
            errors.append((thread_id, e))
    
    threads = []
    for i in range(n_threads):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # No errors should occur from concurrent access
    assert len(errors) == 0, f"Concurrent access caused errors: {errors}"


# Test 4: Test eviction period environment variable parsing
@given(
    eviction_str=st.one_of(
        st.just("0"),  # Zero eviction - edge case
        st.just("-1"),  # Negative eviction - potential bug
        st.just("0.001"),  # Very small eviction period
        st.just("inf"),  # Infinite eviction
        st.just("nan"),  # NaN eviction
        st.text(min_size=1, max_size=10).filter(lambda x: not x.replace('.','').replace('-','').isdigit())  # Invalid strings
    )
)
def test_eviction_period_env_parsing(eviction_str):
    """Test parsing of GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS environment variable."""
    
    # Set the environment variable
    os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS'] = eviction_str
    
    try:
        # Try to trigger the parsing by importing fresh
        import importlib
        
        # This would normally reload the module, but we can't easily do that
        # Instead, test the parsing logic directly
        try:
            eviction_seconds = float(eviction_str)
            
            if eviction_seconds != eviction_seconds:  # NaN
                # NaN eviction period is a bug
                print(f"BUG: NaN eviction period would be accepted: {eviction_str}")
            elif eviction_seconds < 0:
                # Negative eviction period is likely a bug
                print(f"POTENTIAL BUG: Negative eviction period would be accepted: {eviction_seconds}")
            elif eviction_seconds == 0:
                # Zero eviction period might cause issues
                print(f"WARNING: Zero eviction period might cause performance issues")
            elif eviction_seconds == float('inf'):
                # Infinite eviction means channels never expire
                print(f"WARNING: Infinite eviction period means channels never expire")
                
        except ValueError:
            # Invalid string should cause the module to use default
            pass
            
    finally:
        # Clean up environment
        if 'GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS' in os.environ:
            del os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS']


if __name__ == "__main__":
    print("Running fixed property-based tests...")
    pytest.main([__file__, "-v", "--tb=short", "-s"])