import sys
import os
import logging
import re
from unittest.mock import Mock

sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

# Configure minimal Django settings
from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test-secret-key',
    INSTALLED_APPS=['log_request_id'],
    MIDDLEWARE=[],
    ROOT_URLCONF='',
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    LOGGING={
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }
)

import django
django.setup()

from hypothesis import given, strategies as st, assume, settings as hypo_settings
from django.test import RequestFactory
from django.http import HttpResponse

from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware
from log_request_id.filters import RequestIDFilter


print("Starting property-based tests for log_request_id module...\n")

# Test 1: UUID generation length invariant
@given(st.integers(min_value=1, max_value=100))
@hypo_settings(max_examples=100)
def test_uuid_generation_length_invariant(seed):
    """UUID generation should always produce 32-character hex strings."""
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    generated_id = middleware._generate_id()
    
    assert len(generated_id) == 32, f"Generated ID has wrong length: {len(generated_id)}"
    assert all(c in '0123456789abcdef' for c in generated_id), f"Generated ID contains non-hex characters: {generated_id}"

print("Testing UUID generation invariant...")
test_uuid_generation_length_invariant()
print("✓ UUID generation test passed\n")


# Test 2: Request ID persistence  
@given(
    st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    st.booleans()
)
@hypo_settings(max_examples=100)
def test_request_id_persistence(request_id, use_header):
    """Request ID should persist throughout request lifecycle."""
    factory = RequestFactory()
    request = factory.get('/')
    
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    
    # Clear any previous request_id
    try:
        del local.request_id
    except AttributeError:
        pass
    
    if use_header:
        # Temporarily modify settings
        original_header = getattr(settings, 'LOG_REQUEST_ID_HEADER', None)
        settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
        
        request.META['HTTP_X_REQUEST_ID'] = request_id
        middleware.process_request(request)
        
        assert request.id == request_id, f"Request ID mismatch: {request.id} != {request_id}"
        assert local.request_id == request_id, f"Local request ID mismatch: {local.request_id} != {request_id}"
        
        # Restore settings
        if original_header is None:
            delattr(settings, 'LOG_REQUEST_ID_HEADER')
        else:
            settings.LOG_REQUEST_ID_HEADER = original_header
    else:
        middleware.process_request(request)
        assert hasattr(request, 'id'), "Request doesn't have id attribute"
        assert local.request_id == request.id, f"Local and request ID mismatch: {local.request_id} != {request.id}"
        assert len(request.id) == 32, f"Generated request ID has wrong length: {len(request.id)}"

print("Testing request ID persistence...")
test_request_id_persistence()
print("✓ Request ID persistence test passed\n")


# Test 3: Filter always passes
@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False))
))
@hypo_settings(max_examples=100)
def test_filter_always_passes(record_attributes):
    """RequestIDFilter should always return True and add request_id."""
    filter_obj = RequestIDFilter()
    
    record = Mock()
    for key, value in record_attributes.items():
        setattr(record, key, value)
    
    result = filter_obj.filter(record)
    
    assert result is True, "Filter didn't return True"
    assert hasattr(record, 'request_id'), "Filter didn't add request_id attribute"

print("Testing filter behavior...")
test_filter_always_passes()
print("✓ Filter test passed\n")


# Test 4: Log message format
@given(
    st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']),
    st.text(min_size=1, max_size=100).map(lambda s: '/' + s.strip().replace(' ', '_').replace('\n', '_')),
    st.integers(min_value=100, max_value=599)
)
@hypo_settings(max_examples=100)
def test_log_message_format(method, path, status_code):
    """Log message should follow consistent format."""
    factory = RequestFactory()
    request = getattr(factory, method.lower())(path)
    response = HttpResponse()
    response.status_code = status_code
    
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    message = middleware.get_log_message(request, response)
    
    expected_prefix = f"method={method} path={path} status={status_code}"
    assert message.startswith(expected_prefix), f"Message format incorrect: {message}"

print("Testing log message format...")
test_log_message_format()
print("✓ Log message format test passed\n")


# Test 5: Response header property
@given(
    st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
)
@hypo_settings(max_examples=100)
def test_response_header_property(request_id, header_name):
    """Response header should contain the same request ID as the request."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    
    # Temporarily modify settings
    original_log_header = getattr(settings, 'LOG_REQUEST_ID_HEADER', None)
    original_response_header = getattr(settings, 'REQUEST_ID_RESPONSE_HEADER', None)
    
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    settings.REQUEST_ID_RESPONSE_HEADER = header_name
    
    request.META['HTTP_X_REQUEST_ID'] = request_id
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    middleware.process_request(request)
    processed_response = middleware.process_response(request, response)
    
    assert processed_response[header_name] == request_id, f"Response header mismatch: {processed_response.get(header_name)} != {request_id}"
    
    # Restore settings
    if original_log_header is None:
        delattr(settings, 'LOG_REQUEST_ID_HEADER')
    else:
        settings.LOG_REQUEST_ID_HEADER = original_log_header
    
    if original_response_header is None:
        delattr(settings, 'REQUEST_ID_RESPONSE_HEADER')
    else:
        settings.REQUEST_ID_RESPONSE_HEADER = original_response_header

print("Testing response header property...")
test_response_header_property()
print("✓ Response header test passed\n")


# Test 6: Edge case - empty or special header values
@given(st.sampled_from(['', ' ', '\n', '\t', 'None', 'null', '0', '-1']))
@hypo_settings(max_examples=50)
def test_edge_case_header_values(header_value):
    """Test handling of edge case header values."""
    factory = RequestFactory()
    request = factory.get('/')
    
    original_header = getattr(settings, 'LOG_REQUEST_ID_HEADER', None)
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    
    request.META['HTTP_X_REQUEST_ID'] = header_value
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    middleware.process_request(request)
    
    # Should use the header value as-is, even if it's empty or unusual
    assert request.id == header_value, f"Request ID should be '{header_value}' but got '{request.id}'"
    
    # Restore settings
    if original_header is None:
        delattr(settings, 'LOG_REQUEST_ID_HEADER')
    else:
        settings.LOG_REQUEST_ID_HEADER = original_header

print("Testing edge case header values...")
test_edge_case_header_values()
print("✓ Edge case test passed\n")


print("=" * 50)
print("All property-based tests passed successfully! ✅")
print("No bugs found in log_request_id module.")