import sys
import os
import logging
import re

sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testproject.settings')
import django
django.setup()

from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle
from django.test import RequestFactory
from django.http import HttpResponse
from django.conf import settings as django_settings
from unittest.mock import Mock, MagicMock

from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware
from log_request_id.filters import RequestIDFilter


@given(st.integers(min_value=1, max_value=10000))
def test_uuid_generation_length_invariant(seed):
    """UUID generation should always produce 32-character hex strings."""
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    generated_id = middleware._generate_id()
    
    assert len(generated_id) == 32
    assert all(c in '0123456789abcdef' for c in generated_id)


@given(
    st.text(min_size=1, max_size=100).filter(lambda s: s.isalnum()),
    st.booleans()
)
def test_request_id_persistence(request_id, use_header):
    """Request ID should persist throughout request lifecycle."""
    factory = RequestFactory()
    request = factory.get('/')
    
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    
    if use_header:
        with django_settings.configure(
            LOG_REQUEST_ID_HEADER='HTTP_X_REQUEST_ID',
            INSTALLED_APPS=['log_request_id'],
            SECRET_KEY='test'
        ):
            request.META['HTTP_X_REQUEST_ID'] = request_id
            middleware.process_request(request)
            assert request.id == request_id
            assert local.request_id == request_id
    else:
        middleware.process_request(request)
        assert hasattr(request, 'id')
        assert local.request_id == request.id
        assert len(request.id) == 32


@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False))
))
def test_filter_always_passes(record_attributes):
    """RequestIDFilter should always return True and add request_id."""
    filter_obj = RequestIDFilter()
    
    record = Mock()
    for key, value in record_attributes.items():
        setattr(record, key, value)
    
    result = filter_obj.filter(record)
    
    assert result is True
    assert hasattr(record, 'request_id')


@given(
    st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']),
    st.text(min_size=1, max_size=100).map(lambda s: '/' + s.replace(' ', '_')),
    st.integers(min_value=100, max_value=599)
)
def test_log_message_format(method, path, status_code):
    """Log message should follow consistent format."""
    factory = RequestFactory()
    request = getattr(factory, method.lower())(path)
    response = HttpResponse()
    response.status_code = status_code
    
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    message = middleware.get_log_message(request, response)
    
    pattern = r'^method=' + re.escape(method) + r' path=' + re.escape(path) + r' status=' + str(status_code)
    assert re.match(pattern, message)


@given(
    st.text(min_size=1, max_size=100).filter(lambda s: s.isalnum()),
    st.text(min_size=1, max_size=50).filter(lambda s: s.isalnum())
)
def test_response_header_property(request_id, header_name):
    """Response header should contain the same request ID as the request."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    
    with django_settings.configure(
        LOG_REQUEST_ID_HEADER='HTTP_X_REQUEST_ID',
        REQUEST_ID_RESPONSE_HEADER=header_name,
        INSTALLED_APPS=['log_request_id'],
        SECRET_KEY='test'
    ):
        request.META['HTTP_X_REQUEST_ID'] = request_id
        middleware = RequestIDMiddleware(get_response=lambda r: response)
        middleware.process_request(request)
        processed_response = middleware.process_response(request, response)
        
        assert processed_response[header_name] == request_id


@given(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
def test_multiple_request_processing(request_ids):
    """Multiple requests should maintain separate IDs without interference."""
    factory = RequestFactory()
    middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
    
    for i, req_id in enumerate(request_ids):
        request = factory.get(f'/path{i}')
        
        if req_id:
            with django_settings.configure(
                LOG_REQUEST_ID_HEADER='HTTP_X_REQUEST_ID',
                INSTALLED_APPS=['log_request_id'],
                SECRET_KEY='test'
            ):
                request.META['HTTP_X_REQUEST_ID'] = req_id
                middleware.process_request(request)
                assert request.id == req_id
        else:
            middleware.process_request(request)
            assert hasattr(request, 'id')
            assert len(request.id) == 32