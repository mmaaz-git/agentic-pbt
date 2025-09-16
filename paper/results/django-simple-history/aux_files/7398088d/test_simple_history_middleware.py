import sys
import threading
import asyncio
from unittest.mock import Mock, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import hypothesis

from simple_history.middleware import HistoryRequestMiddleware, _context_manager
from simple_history.models import HistoricalRecords


@given(
    request_data=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=0,
        max_size=5
    ),
    response_data=st.one_of(
        st.text(),
        st.integers(),
        st.booleans(),
        st.none(),
        st.dictionaries(st.text(), st.text())
    )
)
def test_middleware_returns_get_response_result(request_data, response_data):
    """Test that middleware always returns exactly what get_response returns"""
    request = Mock()
    for key, value in request_data.items():
        setattr(request, key, value)
    
    def get_response(req):
        assert req is request
        return response_data
    
    middleware = HistoryRequestMiddleware(get_response)
    result = middleware(request)
    
    assert result == response_data, f"Expected {response_data}, got {result}"


@given(
    request_attrs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=5
    ),
    should_raise=st.booleans()
)
def test_context_cleanup_on_exception(request_attrs, should_raise):
    """Test that context is always cleaned up, even when exceptions occur"""
    request = Mock()
    for key, value in request_attrs.items():
        setattr(request, key, value)
    
    initial_has_request = hasattr(HistoricalRecords.context, 'request')
    
    class TestException(Exception):
        pass
    
    def get_response(req):
        assert hasattr(HistoricalRecords.context, 'request')
        assert HistoricalRecords.context.request is request
        if should_raise:
            raise TestException("Test exception")
        return "response"
    
    middleware = HistoryRequestMiddleware(get_response)
    
    try:
        result = middleware(request)
        assert not should_raise
        assert result == "response"
    except TestException:
        assert should_raise
    
    # Context should be cleaned up regardless of exception
    assert hasattr(HistoricalRecords.context, 'request') == initial_has_request


@given(
    num_requests=st.integers(min_value=2, max_value=10),
    request_ids=st.lists(
        st.integers(min_value=0, max_value=1000000),
        min_size=2,
        max_size=10,
        unique=True
    )
)
@settings(max_examples=20, deadline=5000)
def test_concurrent_request_isolation(num_requests, request_ids):
    """Test that concurrent requests maintain isolated contexts"""
    assume(len(request_ids) >= num_requests)
    request_ids = request_ids[:num_requests]
    
    results = []
    errors = []
    
    def process_request(req_id):
        request = Mock()
        request.id = req_id
        
        def get_response(req):
            # Check that the context has the correct request
            if hasattr(HistoricalRecords.context, 'request'):
                ctx_req = HistoricalRecords.context.request
                if ctx_req.id != req_id:
                    return f"ERROR: Expected request {req_id}, got {ctx_req.id}"
            else:
                return f"ERROR: No request in context for {req_id}"
            return f"SUCCESS_{req_id}"
        
        middleware = HistoryRequestMiddleware(get_response)
        return middleware(request)
    
    with ThreadPoolExecutor(max_workers=min(num_requests, 5)) as executor:
        futures = {executor.submit(process_request, req_id): req_id 
                  for req_id in request_ids}
        
        for future in as_completed(futures):
            result = future.result()
            if result.startswith("ERROR"):
                errors.append(result)
            results.append(result)
    
    assert not errors, f"Context isolation violated: {errors}"
    
    # Verify all requests were processed successfully
    for req_id in request_ids:
        assert f"SUCCESS_{req_id}" in results


@given(
    request_attrs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.text(), st.integers()),
        min_size=0,
        max_size=3
    )
)
def test_context_manager_cleanup_invariant(request_attrs):
    """Test that _context_manager always cleans up the request attribute"""
    request = Mock()
    for key, value in request_attrs.items():
        setattr(request, key, value)
    
    # Save initial state
    initial_has_request = hasattr(HistoricalRecords.context, 'request')
    initial_request = getattr(HistoricalRecords.context, 'request', None) if initial_has_request else None
    
    # Use context manager
    with _context_manager(request):
        assert hasattr(HistoricalRecords.context, 'request')
        assert HistoricalRecords.context.request is request
    
    # After exiting, state should be restored
    if initial_has_request:
        assert hasattr(HistoricalRecords.context, 'request')
        assert HistoricalRecords.context.request == initial_request
    else:
        assert not hasattr(HistoricalRecords.context, 'request')


@given(
    response_value=st.one_of(
        st.text(),
        st.integers(),
        st.dictionaries(st.text(), st.text()),
        st.lists(st.integers())
    )
)
@settings(max_examples=100)
def test_async_middleware_returns_response(response_value):
    """Test async middleware correctly returns get_response result"""
    request = Mock()
    
    async def async_get_response(req):
        assert req is request
        return response_value
    
    # Create async middleware
    async_middleware = HistoryRequestMiddleware(async_get_response)
    
    # Run async test
    async def run_test():
        result = await async_middleware(request)
        assert result == response_value
    
    asyncio.run(run_test())


@given(
    should_delete_during_request=st.booleans()
)
def test_double_deletion_handling(should_delete_during_request):
    """Test that middleware handles double deletion gracefully"""
    request = Mock()
    
    def get_response(req):
        if should_delete_during_request:
            # Simulate something else deleting the request
            if hasattr(HistoricalRecords.context, 'request'):
                del HistoricalRecords.context.request
        return "response"
    
    middleware = HistoryRequestMiddleware(get_response)
    
    # Should not raise AttributeError even if already deleted
    result = middleware(request)
    assert result == "response"
    
    # Context should be clean after middleware
    assert not hasattr(HistoricalRecords.context, 'request')