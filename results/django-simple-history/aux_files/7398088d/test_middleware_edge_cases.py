import sys
import threading
import asyncio
import time
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, note
import hypothesis

from simple_history.middleware import HistoryRequestMiddleware, _context_manager
from simple_history.models import HistoricalRecords


@given(
    num_sequential_calls=st.integers(min_value=2, max_value=10),
    request_ids=st.lists(st.integers(), min_size=2, max_size=10, unique=True)
)
def test_sequential_middleware_reuse(num_sequential_calls, request_ids):
    """Test that the same middleware instance can be reused for multiple requests"""
    assume(len(request_ids) >= num_sequential_calls)
    request_ids = request_ids[:num_sequential_calls]
    
    responses_seen = []
    
    def get_response(req):
        # Verify context has correct request
        assert hasattr(HistoricalRecords.context, 'request')
        assert HistoricalRecords.context.request.id == req.id
        response = f"response_{req.id}"
        responses_seen.append(response)
        return response
    
    # Create middleware once
    middleware = HistoryRequestMiddleware(get_response)
    
    # Use it multiple times
    for req_id in request_ids:
        request = Mock()
        request.id = req_id
        
        result = middleware(request)
        assert result == f"response_{req_id}"
        
        # Context should be clean after each call
        assert not hasattr(HistoricalRecords.context, 'request')
    
    assert len(responses_seen) == num_sequential_calls


@given(
    nested_depth=st.integers(min_value=1, max_value=5)
)
def test_nested_context_managers(nested_depth):
    """Test that nested context managers don't interfere with each other"""
    requests = [Mock() for _ in range(nested_depth)]
    for i, req in enumerate(requests):
        req.id = i
    
    def nested_test(depth, remaining_requests):
        if not remaining_requests:
            # At deepest level, all requests should be in context
            # But only the most recent one should be accessible
            assert hasattr(HistoricalRecords.context, 'request')
            assert HistoricalRecords.context.request.id == depth - 1
            return
        
        current_request = remaining_requests[0]
        with _context_manager(current_request):
            assert HistoricalRecords.context.request is current_request
            nested_test(depth, remaining_requests[1:])
            # After returning from nested call, should still have current request
            assert HistoricalRecords.context.request is current_request
    
    initial_state = hasattr(HistoricalRecords.context, 'request')
    nested_test(nested_depth, requests)
    
    # After all nested calls, context should be clean
    assert hasattr(HistoricalRecords.context, 'request') == initial_state


@given(
    exception_type=st.sampled_from([ValueError, TypeError, KeyError, AttributeError]),
    exception_message=st.text(min_size=0, max_size=100)
)
def test_various_exception_types(exception_type, exception_message):
    """Test that context cleanup works with various exception types"""
    request = Mock()
    
    def get_response(req):
        assert HistoricalRecords.context.request is request
        raise exception_type(exception_message)
    
    middleware = HistoryRequestMiddleware(get_response)
    
    try:
        middleware(request)
        assert False, "Should have raised exception"
    except exception_type as e:
        assert str(e) == exception_message
    
    # Context should be cleaned up
    assert not hasattr(HistoricalRecords.context, 'request')


@given(
    request_attr_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=97)),
    request_attr_value=st.one_of(st.integers(), st.text(), st.none())
)
def test_context_attribute_preservation(request_attr_name, request_attr_value):
    """Test that modifying request attributes during middleware doesn't affect context"""
    request = Mock()
    setattr(request, request_attr_name, request_attr_value)
    
    def get_response(req):
        # Verify initial state
        assert hasattr(HistoricalRecords.context, 'request')
        assert getattr(HistoricalRecords.context.request, request_attr_name, None) == request_attr_value
        
        # Modify the request attribute
        new_value = "modified"
        setattr(req, request_attr_name, new_value)
        
        # Context should see the modification (same object)
        assert getattr(HistoricalRecords.context.request, request_attr_name) == new_value
        return "response"
    
    middleware = HistoryRequestMiddleware(get_response)
    result = middleware(request)
    
    assert result == "response"
    assert not hasattr(HistoricalRecords.context, 'request')


@given(
    should_raise=st.booleans(),
    delay_ms=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=50, deadline=2000)
def test_async_exception_handling(should_raise, delay_ms):
    """Test async middleware exception handling and cleanup"""
    request = Mock()
    request.id = "async_test"
    
    class AsyncException(Exception):
        pass
    
    async def async_get_response(req):
        assert HistoricalRecords.context.request is request
        await asyncio.sleep(delay_ms / 1000.0)
        if should_raise:
            raise AsyncException("Async error")
        return "async_response"
    
    middleware = HistoryRequestMiddleware(async_get_response)
    
    async def run_test():
        try:
            result = await middleware(request)
            assert not should_raise
            assert result == "async_response"
        except AsyncException:
            assert should_raise
        
        # Context should be clean
        assert not hasattr(HistoricalRecords.context, 'request')
    
    asyncio.run(run_test())


@given(
    middleware_count=st.integers(min_value=1, max_value=5),
    request_data=st.text(min_size=1, max_size=20)
)
def test_chained_middleware(middleware_count, request_data):
    """Test multiple HistoryRequestMiddleware instances chained together"""
    request = Mock()
    request.data = request_data
    
    def final_handler(req):
        # All middleware should set the same context
        assert hasattr(HistoricalRecords.context, 'request')
        assert HistoricalRecords.context.request.data == request_data
        return f"final_{request_data}"
    
    # Chain multiple middleware instances
    handler = final_handler
    for i in range(middleware_count):
        handler = HistoryRequestMiddleware(handler)
    
    result = handler(request)
    assert result == f"final_{request_data}"
    
    # Context should be clean after all middleware
    assert not hasattr(HistoricalRecords.context, 'request')


@given(
    set_context_before=st.booleans()
)
def test_pre_existing_context(set_context_before):
    """Test middleware behavior when context already has a request"""
    old_request = Mock()
    old_request.id = "old"
    new_request = Mock()
    new_request.id = "new"
    
    if set_context_before:
        HistoricalRecords.context.request = old_request
    
    def get_response(req):
        assert HistoricalRecords.context.request is new_request
        return "response"
    
    middleware = HistoryRequestMiddleware(get_response)
    result = middleware(new_request)
    
    assert result == "response"
    
    # After middleware, old context should be restored or cleaned
    if set_context_before:
        # This is the potential bug - does it restore the old request?
        # According to the implementation, it just deletes, doesn't restore
        assert not hasattr(HistoricalRecords.context, 'request')
    else:
        assert not hasattr(HistoricalRecords.context, 'request')