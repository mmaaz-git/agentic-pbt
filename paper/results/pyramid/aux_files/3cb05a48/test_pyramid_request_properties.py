#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize
import pyramid.request
from pyramid.request import Request, CallbackMethodsMixin
from pyramid.response import Response
from pyramid.registry import Registry
from collections import deque
import weakref


# Test 1: Callback queue FIFO order property
@given(st.lists(st.integers(), min_size=1, max_size=100))
def test_response_callbacks_fifo_order(callback_ids):
    """Response callbacks should be called in FIFO order (first added, first called)"""
    request = Request.blank('/')
    request.registry = Registry()
    
    call_order = []
    
    # Add callbacks with unique IDs
    for cb_id in callback_ids:
        def make_callback(cb_id):
            def callback(req, resp):
                call_order.append(cb_id)
            return callback
        request.add_response_callback(make_callback(cb_id))
    
    # Process callbacks
    dummy_response = Response()
    request._process_response_callbacks(dummy_response)
    
    # Check FIFO order
    assert call_order == callback_ids, f"Expected {callback_ids}, got {call_order}"


@given(st.lists(st.integers(), min_size=1, max_size=100))
def test_finished_callbacks_fifo_order(callback_ids):
    """Finished callbacks should be called in FIFO order (first added, first called)"""
    request = Request.blank('/')
    request.registry = Registry()
    
    call_order = []
    
    # Add callbacks with unique IDs
    for cb_id in callback_ids:
        def make_callback(cb_id):
            def callback(req):
                call_order.append(cb_id)
            return callback
        request.add_finished_callback(make_callback(cb_id))
    
    # Process callbacks
    request._process_finished_callbacks()
    
    # Check FIFO order
    assert call_order == callback_ids, f"Expected {callback_ids}, got {call_order}"


# Test 2: Callback queue emptying property
@given(st.lists(st.integers(), min_size=0, max_size=50))
def test_response_callbacks_queue_empties(callback_ids):
    """Response callbacks queue should be empty after processing"""
    request = Request.blank('/')
    request.registry = Registry()
    
    # Add callbacks
    for _ in callback_ids:
        request.add_response_callback(lambda req, resp: None)
    
    # Check queue has expected size
    assert len(request.response_callbacks) == len(callback_ids)
    
    # Process callbacks
    dummy_response = Response()
    request._process_response_callbacks(dummy_response)
    
    # Queue should be empty
    assert len(request.response_callbacks) == 0, "Queue should be empty after processing"


@given(st.lists(st.integers(), min_size=0, max_size=50))
def test_finished_callbacks_queue_empties(callback_ids):
    """Finished callbacks queue should be empty after processing"""
    request = Request.blank('/')
    request.registry = Registry()
    
    # Add callbacks
    for _ in callback_ids:
        request.add_finished_callback(lambda req: None)
    
    # Check queue has expected size
    assert len(request.finished_callbacks) == len(callback_ids)
    
    # Process callbacks
    request._process_finished_callbacks()
    
    # Queue should be empty
    assert len(request.finished_callbacks) == 0, "Queue should be empty after processing"


# Test 3: URL port normalization properties
@given(
    scheme=st.sampled_from(['http', 'https', None]),
    host=st.sampled_from(['example.com', 'localhost', '127.0.0.1']),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535).map(str))
)
def test_partial_application_url_port_normalization(scheme, host, port):
    """Test that default ports are normalized correctly for http/https"""
    request = Request.blank('/')
    request.environ['wsgi.url_scheme'] = 'http'
    request.environ['SERVER_NAME'] = 'original.com'
    request.environ['SERVER_PORT'] = '8080'
    
    url = request._partial_application_url(scheme=scheme, host=host, port=port)
    
    # Property: Default ports should not appear in URL
    if scheme == 'http' and port == '80':
        assert ':80' not in url, f"Default HTTP port should not appear in URL: {url}"
    elif scheme == 'https' and port == '443':
        assert ':443' not in url, f"Default HTTPS port should not appear in URL: {url}"
    
    # Property: Non-default ports should appear
    if port and port not in ['80', '443']:
        assert f':{port}' in url, f"Non-default port {port} should appear in URL: {url}"
    
    # Property: Scheme should be in URL
    if scheme:
        assert url.startswith(f'{scheme}://'), f"URL should start with {scheme}://"


# Test 4: Response object recognition
@given(st.data())
def test_is_response_with_response_objects(data):
    """Test that is_response correctly identifies Response objects"""
    request = Request.blank('/')
    request.registry = Registry()
    
    # Test with actual Response objects
    response = Response()
    assert request.is_response(response) == True, "Should recognize Response object"
    
    # Test with non-Response objects
    non_responses = [
        None,
        42,
        "string",
        [],
        {},
        object(),
    ]
    
    for obj in non_responses:
        result = request.is_response(obj)
        assert result == False, f"Should not recognize {type(obj)} as Response"


# Test 5: Callback exception handling property
@given(
    num_callbacks=st.integers(min_value=2, max_value=10),
    failing_index=st.integers(min_value=0)
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_callback_exception_propagation(num_callbacks, failing_index):
    """Test that exceptions in callbacks are propagated and stop further processing"""
    failing_index = failing_index % num_callbacks  # Ensure it's within range
    
    request = Request.blank('/')
    request.registry = Registry()
    
    call_order = []
    
    # Add callbacks, one will raise exception
    for i in range(num_callbacks):
        def make_callback(idx):
            def callback(req, resp):
                call_order.append(idx)
                if idx == failing_index:
                    raise ValueError(f"Callback {idx} failed")
            return callback
        request.add_response_callback(make_callback(i))
    
    # Process callbacks and expect exception
    dummy_response = Response()
    try:
        request._process_response_callbacks(dummy_response)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert f"Callback {failing_index} failed" in str(e)
    
    # Only callbacks up to and including the failing one should have been called
    assert call_order == list(range(failing_index + 1)), \
        f"Expected callbacks 0-{failing_index} to be called, got {call_order}"


# Test 6: Multiple callback additions preserve order
@given(st.lists(st.lists(st.integers(), min_size=1, max_size=5), min_size=1, max_size=5))
def test_multiple_batch_additions_preserve_order(batches):
    """Adding callbacks in multiple batches should preserve overall FIFO order"""
    request = Request.blank('/')
    request.registry = Registry()
    
    expected_order = []
    call_order = []
    
    # Add callbacks in batches
    for batch in batches:
        for cb_id in batch:
            expected_order.append(cb_id)
            def make_callback(cb_id):
                def callback(req, resp):
                    call_order.append(cb_id)
                return callback
            request.add_response_callback(make_callback(cb_id))
    
    # Process all callbacks
    dummy_response = Response()
    request._process_response_callbacks(dummy_response)
    
    # Check order is preserved
    assert call_order == expected_order, \
        f"Batch additions should preserve order. Expected {expected_order}, got {call_order}"


if __name__ == "__main__":
    print("Running property-based tests for pyramid.request...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])