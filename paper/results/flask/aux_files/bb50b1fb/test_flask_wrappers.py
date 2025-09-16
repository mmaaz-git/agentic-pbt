"""Property-based tests for flask.wrappers module."""

import json
from hypothesis import given, strategies as st, assume, settings
from flask import Response, Request
from werkzeug.test import EnvironBuilder
import math


# Strategy for generating valid JSON-serializable data
json_strategy = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            children,
            max_size=10
        ),
    ),
    max_leaves=50
)


@given(json_strategy)
def test_response_json_roundtrip(data):
    """Test that Response JSON data can be round-tripped."""
    # Create a Response with JSON data
    json_str = json.dumps(data)
    response = Response(json_str, content_type='application/json')
    
    # Parse the JSON back
    parsed = response.get_json()
    
    # The parsed data should equal the original
    assert parsed == data


@given(json_strategy)
def test_response_json_content_type_consistency(data):
    """Test that is_json property is consistent with content_type."""
    # Create Response with JSON data and application/json content type
    json_str = json.dumps(data)
    response = Response(json_str, content_type='application/json')
    
    # If is_json is True, content_type should contain 'application/json'
    if response.is_json:
        assert 'application/json' in response.content_type
    
    # Test with explicit non-JSON content type
    response2 = Response(json_str, content_type='text/plain')
    if not response2.is_json:
        assert 'application/json' not in response2.content_type


@given(st.text(min_size=1, max_size=50))
def test_response_content_encoding_header_property(encoding):
    """Test that content_encoding header property works correctly."""
    response = Response()
    
    # Set the content encoding
    response.content_encoding = encoding
    
    # Should be retrievable
    assert response.content_encoding == encoding
    
    # Should be in headers
    assert response.headers.get('Content-Encoding') == encoding


@given(st.text(min_size=1, max_size=100))
def test_response_content_md5_header_property(md5_value):
    """Test that content_md5 header property works correctly."""
    response = Response()
    
    # Set the MD5 value
    response.content_md5 = md5_value
    
    # Should be retrievable
    assert response.content_md5 == md5_value
    
    # Should be in headers
    assert response.headers.get('Content-MD5') == md5_value


@given(st.integers(min_value=0, max_value=1000000))
def test_response_content_length_consistency(length):
    """Test content_length property consistency."""
    response = Response()
    
    # Set content length
    response.content_length = length
    
    # Should be retrievable
    assert response.content_length == length
    
    # Should be in headers as string
    assert response.headers.get('Content-Length') == str(length)


@given(st.text(min_size=1, max_size=50))
def test_response_access_control_allow_origin(origin):
    """Test access_control_allow_origin header property."""
    response = Response()
    
    # Set the origin
    response.access_control_allow_origin = origin
    
    # Should be retrievable
    assert response.access_control_allow_origin == origin
    
    # Should be in headers
    assert response.headers.get('Access-Control-Allow-Origin') == origin


@given(json_strategy)
def test_response_json_force_parse(data):
    """Test that force=True allows parsing JSON regardless of content type."""
    json_str = json.dumps(data)
    
    # Create response with non-JSON content type
    response = Response(json_str, content_type='text/plain')
    
    # Without force, might return None if not JSON content type
    # With force=True, should parse the JSON
    parsed = response.get_json(force=True)
    assert parsed == data


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=10
))
def test_request_json_roundtrip_with_environ(data):
    """Test Request JSON parsing from WSGI environ."""
    json_str = json.dumps(data)
    
    # Create a proper WSGI environ with JSON data
    builder = EnvironBuilder(method='POST', data=json_str, content_type='application/json')
    environ = builder.get_environ()
    
    # Create Request from environ
    request = Request(environ)
    
    # Parse JSON
    parsed = request.get_json()
    
    # Should match original data
    assert parsed == data


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=10
))
def test_request_json_caching(data):
    """Test that Request JSON caching works correctly."""
    json_str = json.dumps(data)
    
    # Create a proper WSGI environ with JSON data
    builder = EnvironBuilder(method='POST', data=json_str, content_type='application/json')
    environ = builder.get_environ()
    
    # Create Request from environ
    request = Request(environ)
    
    # First call with cache=True (default)
    parsed1 = request.get_json(cache=True)
    
    # Second call should return the same cached object
    parsed2 = request.get_json(cache=True)
    
    # They should be the exact same object (identity check)
    assert parsed1 is parsed2
    assert parsed1 == data


@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5))
def test_response_access_control_allow_methods(methods):
    """Test access_control_allow_methods header property."""
    response = Response()
    
    # Set the methods (can be a list)
    methods_str = ', '.join(methods)
    response.access_control_allow_methods = methods_str
    
    # Should be retrievable
    assert response.access_control_allow_methods == methods_str
    
    # Should be in headers
    assert response.headers.get('Access-Control-Allow-Methods') == methods_str


if __name__ == "__main__":
    # Run a simple check
    import pytest
    pytest.main([__file__, "-v"])