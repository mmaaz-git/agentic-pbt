import sys
import logging
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=['log_request_id'],
    MIDDLEWARE=[],
)

import django
django.setup()

from hypothesis import given, strategies as st, assume, settings as hypo_settings
from django.test import RequestFactory
from django.http import HttpResponse
from unittest.mock import Mock, patch

from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware
from log_request_id.filters import RequestIDFilter

print("Running advanced property-based tests...\n")

# Test 1: Concurrent request handling
@given(st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=10))
@hypo_settings(max_examples=50)
def test_concurrent_request_isolation(request_ids):
    """Each request should maintain its own ID without interference."""
    factory = RequestFactory()
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    
    requests = []
    for i, req_id in enumerate(request_ids):
        request = factory.get(f'/path{i}')
        request.META['HTTP_X_REQUEST_ID'] = req_id
        middleware.process_request(request)
        requests.append((request, req_id))
    
    # Verify each request still has its correct ID
    for request, expected_id in requests:
        assert request.id == expected_id, f"Request ID changed: expected {expected_id}, got {request.id}"

print("Testing concurrent request isolation...")
test_concurrent_request_isolation()
print("✓ Concurrent request test passed\n")


# Test 2: Settings interaction - GENERATE_REQUEST_ID_IF_NOT_IN_HEADER
@given(st.booleans())
@hypo_settings(max_examples=50)
def test_generate_if_not_in_header_setting(should_generate):
    """Test GENERATE_REQUEST_ID_IF_NOT_IN_HEADER setting behavior."""
    factory = RequestFactory()
    request = factory.get('/')
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    settings.GENERATE_REQUEST_ID_IF_NOT_IN_HEADER = should_generate
    
    # Don't provide the header
    middleware.process_request(request)
    
    if should_generate:
        # Should generate an ID
        assert len(request.id) == 32, f"Expected generated ID, got: {request.id}"
        assert all(c in '0123456789abcdef' for c in request.id)
    else:
        # Should use default
        assert request.id == 'none', f"Expected 'none', got: {request.id}"
    
    # Clean up settings
    delattr(settings, 'GENERATE_REQUEST_ID_IF_NOT_IN_HEADER')

print("Testing GENERATE_REQUEST_ID_IF_NOT_IN_HEADER setting...")
test_generate_if_not_in_header_setting()
print("✓ Generate if not in header test passed\n")


# Test 3: Process response cleanup
@given(st.text(min_size=1, max_size=50))
@hypo_settings(max_examples=50)
def test_local_cleanup_after_response(request_id):
    """local.request_id should be cleaned up after process_response."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    request.META['HTTP_X_REQUEST_ID'] = request_id
    
    # Process request - should set local.request_id
    middleware.process_request(request)
    assert local.request_id == request_id
    
    # Process response - should clean up local.request_id
    middleware.process_response(request, response)
    assert not hasattr(local, 'request_id'), "local.request_id not cleaned up after response"

print("Testing local cleanup after response...")
test_local_cleanup_after_response()
print("✓ Local cleanup test passed\n")


# Test 4: User attribute edge cases
@given(
    st.one_of(
        st.none(),
        st.just(False),
        st.just(''),
        st.text(min_size=1, max_size=20)
    )
)
@hypo_settings(max_examples=50)
def test_user_attribute_setting(user_attr):
    """Test LOG_USER_ATTRIBUTE setting with various values."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    response.status_code = 200
    
    # Create a mock user
    user = Mock()
    user.pk = 'test_pk'
    user.username = 'test_username'
    user.id = 'test_id'
    request.user = user
    
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    
    settings.LOG_USER_ATTRIBUTE = user_attr
    message = middleware.get_log_message(request, response)
    
    if user_attr in (None, False, ''):
        # Should not include user info
        assert 'user=' not in message, f"User info shouldn't be in message when LOG_USER_ATTRIBUTE={user_attr!r}"
    elif hasattr(user, user_attr):
        # Should include the specified attribute
        expected_value = getattr(user, user_attr)
        assert f'user={expected_value}' in message
    else:
        # Should fall back to user.id
        assert 'user=test_id' in message
    
    # Clean up
    if hasattr(settings, 'LOG_USER_ATTRIBUTE'):
        delattr(settings, 'LOG_USER_ATTRIBUTE')

print("Testing LOG_USER_ATTRIBUTE setting...")
test_user_attribute_setting()
print("✓ User attribute test passed\n")


# Test 5: Response header with missing request.id
@given(st.text(min_size=1, max_size=50))
@hypo_settings(max_examples=50)
def test_response_header_without_request_id(header_name):
    """Response header should not be set if request.id is missing."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    
    # Don't call process_request, so request.id won't be set
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    
    settings.REQUEST_ID_RESPONSE_HEADER = header_name
    
    middleware.process_response(request, response)
    
    # Response should not have the header
    assert not response.has_header(header_name), f"Response header {header_name} should not be set without request.id"
    
    # Clean up
    if hasattr(settings, 'REQUEST_ID_RESPONSE_HEADER'):
        delattr(settings, 'REQUEST_ID_RESPONSE_HEADER')

print("Testing response header without request.id...")
test_response_header_without_request_id()
print("✓ Response header without request.id test passed\n")


# Test 6: Favicon path exclusion
@given(st.text().filter(lambda s: 'favicon' in s))
@hypo_settings(max_examples=50)
def test_favicon_exclusion(path_with_favicon):
    """Requests with 'favicon' in path should not be logged."""
    factory = RequestFactory()
    request = factory.get(f'/{path_with_favicon}')
    response = HttpResponse()
    response.status_code = 200
    
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    middleware.process_request(request)
    
    settings.LOG_REQUESTS = True
    
    # Mock the logger
    with patch('log_request_id.middleware.logger') as mock_logger:
        middleware.process_response(request, response)
        # Logger should not be called for favicon paths
        mock_logger.info.assert_not_called()
    
    # Clean up
    if hasattr(settings, 'LOG_REQUESTS'):
        delattr(settings, 'LOG_REQUESTS')

print("Testing favicon exclusion...")
test_favicon_exclusion()
print("✓ Favicon exclusion test passed\n")


# Test 7: Custom NO_REQUEST_ID setting
@given(st.text(min_size=1, max_size=50))
@hypo_settings(max_examples=50)
def test_custom_no_request_id(custom_default):
    """Test custom NO_REQUEST_ID setting."""
    settings.NO_REQUEST_ID = custom_default
    
    filter_obj = RequestIDFilter()
    record = Mock()
    
    # When local.request_id is not set, should use custom default
    if hasattr(local, 'request_id'):
        del local.request_id
    
    filter_obj.filter(record)
    assert record.request_id == custom_default, f"Expected {custom_default!r}, got {record.request_id!r}"
    
    # Clean up
    if hasattr(settings, 'NO_REQUEST_ID'):
        delattr(settings, 'NO_REQUEST_ID')

print("Testing custom NO_REQUEST_ID setting...")
test_custom_no_request_id()
print("✓ Custom NO_REQUEST_ID test passed\n")


print("=" * 50)
print("All advanced property tests passed! ✅")
print("No bugs found in the middleware.")