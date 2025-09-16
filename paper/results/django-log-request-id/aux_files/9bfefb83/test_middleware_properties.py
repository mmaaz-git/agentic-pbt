#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')
sys.path.insert(0, '/root/hypothesis-llm/worker_/14')

# Setup Django settings before importing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
import django
django.setup()

import re
from unittest import mock
from hypothesis import given, strategies as st, assume, settings
from django.test import RequestFactory
from django.http import HttpResponse
from django.conf import settings as django_settings
from log_request_id.middleware import RequestIDMiddleware
from log_request_id import DEFAULT_NO_REQUEST_ID


# Property 1: UUID generation should always return a valid 32-char hex string
@given(st.integers(min_value=0, max_value=100))
def test_uuid_generation_invariant(n):
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    # Generate multiple IDs to test uniqueness and format
    ids = [middleware._generate_id() for _ in range(n)]
    
    for request_id in ids:
        # Should be a 32-character hex string (uuid4().hex format)
        assert isinstance(request_id, str)
        assert len(request_id) == 32
        assert all(c in '0123456789abcdef' for c in request_id)
    
    # All generated IDs should be unique
    if n > 1:
        assert len(set(ids)) == len(ids), "Generated IDs should be unique"


# Property 2: Request ID assignment - after process_request, request should have an id
@given(st.text(min_size=1, max_size=200), st.text(min_size=1, max_size=200))
def test_request_id_assignment(method, path):
    assume('/' in path or path == '')  # Ensure path is somewhat valid
    
    factory = RequestFactory()
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    # Create a request
    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
        request_method = getattr(factory, method.lower(), factory.get)
    else:
        request_method = factory.get
    
    request = request_method('/' + path.lstrip('/'))
    
    # Process the request
    middleware.process_request(request)
    
    # Request should now have an id attribute
    assert hasattr(request, 'id')
    assert request.id is not None
    assert isinstance(request.id, str)
    assert len(request.id) > 0


# Property 3: Header-based ID - if header is configured and present, use that exact value
@given(st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
       st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_header_based_id_property(header_name, header_value):
    # Ensure header_name is a valid Django META key format
    meta_key = 'HTTP_' + header_name.upper().replace('-', '_')
    
    factory = RequestFactory()
    
    with mock.patch.object(django_settings, 'LOG_REQUEST_ID_HEADER', header_name):
        middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
        
        request = factory.get('/')
        request.META[meta_key] = header_value
        
        middleware.process_request(request)
        
        # The request ID should be exactly the header value
        assert request.id == header_value
        assert hasattr(request, 'id')


# Property 4: Log message format should follow the pattern
@given(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
       st.text(min_size=1, max_size=100).map(lambda x: '/' + x.lstrip('/')),
       st.integers(min_value=100, max_value=599))
def test_log_message_format(method, path, status_code):
    factory = RequestFactory()
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = getattr(factory, method.lower())('/' + path.lstrip('/'))
    response = HttpResponse(status=status_code)
    
    log_message = middleware.get_log_message(request, response)
    
    # Check the log message format: method=X path=Y status=Z
    expected_pattern = f'method={method} path=/{path.lstrip("/")} status={status_code}'
    assert log_message.startswith(expected_pattern)


# Property 5: Response header setting - if configured, response should contain the header
@given(st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
       st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()))
@settings(max_examples=50)
def test_response_header_property(response_header_name, request_id):
    factory = RequestFactory()
    
    with mock.patch.object(django_settings, 'REQUEST_ID_RESPONSE_HEADER', response_header_name):
        middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
        
        request = factory.get('/')
        request.id = request_id  # Simulate that process_request already set this
        
        response = HttpResponse()
        result = middleware.process_response(request, response)
        
        # The response should have the configured header with the request ID
        assert result.has_header(response_header_name)
        assert result[response_header_name] == request_id


# Property 6: Fallback behavior when header is configured but not present
@given(st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').isalnum()),
       st.booleans())
def test_fallback_behavior(header_name, generate_if_missing):
    factory = RequestFactory()
    
    with mock.patch.object(django_settings, 'LOG_REQUEST_ID_HEADER', header_name):
        with mock.patch.object(django_settings, 'GENERATE_REQUEST_ID_IF_NOT_IN_HEADER', generate_if_missing):
            middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
            
            request = factory.get('/')
            # Don't set the header - it's missing
            
            middleware.process_request(request)
            
            if generate_if_missing:
                # Should generate a new UUID
                assert len(request.id) == 32
                assert all(c in '0123456789abcdef' for c in request.id)
            else:
                # Should use DEFAULT_NO_REQUEST_ID
                assert request.id == DEFAULT_NO_REQUEST_ID


# Property 7: get_log_message with user attribute handling
@given(st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
       st.text(min_size=1, max_size=50))
def test_log_message_user_attribute(attribute_name, attribute_value):
    factory = RequestFactory()
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    with mock.patch.object(django_settings, 'LOG_USER_ATTRIBUTE', attribute_name):
        request = factory.get('/')
        response = HttpResponse(status=200)
        
        # Create a mock user with the attribute
        mock_user = mock.Mock()
        setattr(mock_user, attribute_name, attribute_value)
        request.user = mock_user
        
        # Mock session to avoid the is_empty check
        request.session = mock.Mock()
        request.session.is_empty.return_value = False
        
        log_message = middleware.get_log_message(request, response)
        
        # The log message should contain the user attribute value
        assert f'user={attribute_value}' in log_message


if __name__ == '__main__':
    print("Running property-based tests for log_request_id.middleware...")
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])