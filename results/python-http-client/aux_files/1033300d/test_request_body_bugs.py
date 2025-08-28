#!/usr/bin/env python3
"""Test for bugs in request body handling"""

import sys
import json
from hypothesis import given, strategies as st, settings

sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client, Response
from python_http_client.exceptions import HTTPError


class MockResponse:
    """Mock response object for testing Response class"""
    def __init__(self, status_code, body, headers=None):
        self._status_code = status_code
        self._body = body
        self._headers = headers or {}
    
    def getcode(self):
        return self._status_code
    
    def read(self):
        return self._body
    
    def info(self):
        return self._headers


# Test 1: Response with empty body but non-None
def test_response_empty_bytes():
    """Test Response.to_dict with empty bytes (not None)"""
    mock_resp = MockResponse(200, b'')
    response = Response(mock_resp)
    
    # Empty body should return None from to_dict
    assert response.to_dict is None
    assert response.body == b''


# Test 2: Response.to_dict with whitespace-only JSON
@given(st.sampled_from([b' ', b'\n', b'\t', b'  \n  ', b'\r\n']))
def test_response_whitespace_only(whitespace):
    """Test Response.to_dict with whitespace-only body"""
    mock_resp = MockResponse(200, whitespace)
    response = Response(mock_resp)
    
    try:
        result = response.to_dict
        # Whitespace-only should fail JSON parsing
        print(f"Unexpected success with whitespace: {whitespace!r}, result: {result}")
    except json.JSONDecodeError:
        pass  # Expected


# Test 3: HTTPError with bytes that can't decode to UTF-8
def test_httperror_invalid_utf8():
    """Test HTTPError.to_dict with invalid UTF-8 bytes"""
    # Invalid UTF-8 sequence
    invalid_utf8 = b'\x80\x81\x82\x83'
    
    error = HTTPError(400, "Bad Request", invalid_utf8, {})
    
    try:
        result = error.to_dict
        print(f"Unexpected success with invalid UTF-8: {invalid_utf8!r}, result: {result}")
    except UnicodeDecodeError:
        pass  # Expected


# Test 4: Response with valid JSON but containing control characters
def test_response_json_with_control_chars():
    """Test Response.to_dict with JSON containing control characters"""
    # JSON with control characters (should be escaped in valid JSON)
    test_cases = [
        b'{"text": "Hello\x00World"}',  # Null byte
        b'{"text": "Line1\x01Line2"}',  # SOH control character
        b'{"text": "Tab\x09here"}',     # Tab (should actually work)
        b'{"text": "New\nline"}',        # Newline (should work)
    ]
    
    for json_bytes in test_cases:
        mock_resp = MockResponse(200, json_bytes)
        response = Response(mock_resp)
        
        try:
            result = response.to_dict
            # Some control characters are valid in JSON strings
            if b'\x00' in json_bytes or b'\x01' in json_bytes:
                print(f"Unexpected success with control char: {json_bytes!r}, result: {result}")
        except json.JSONDecodeError:
            # Control characters should cause decode errors
            if b'\x09' in json_bytes or b'\n' in json_bytes:
                print(f"Unexpected failure with valid control char: {json_bytes!r}")


# Test 5: Client URL building with query params containing special values
def test_client_special_query_values():
    """Test Client._build_url with special query parameter values"""
    special_cases = [
        {'key': None},  # None value
        {'key': []},    # Empty list
        {'key': [1, 2, 3]},  # List of integers
        {'key': {'nested': 'dict'}},  # Nested dict
        {'key': True},  # Boolean
        {'key': 1.5},   # Float
    ]
    
    client = Client(host='http://test')
    
    for params in special_cases:
        try:
            url = client._build_url(params)
            print(f"Params: {params}")
            print(f"  URL: {url}")
            # Should handle these somehow
            assert 'http://test' in url
        except Exception as e:
            print(f"Error with params {params}: {e}")


# Test 6: Response body that looks like JSON but isn't
def test_response_json_like_but_invalid():
    """Test Response.to_dict with JSON-like but invalid content"""
    test_cases = [
        b'{key: "value"}',        # Missing quotes on key
        b"{'key': 'value'}",      # Single quotes instead of double
        b'{"key": undefined}',    # JavaScript undefined
        b'{"key": NaN}',          # NaN literal
        b'{"key": Infinity}',     # Infinity literal
        b'{/*comment*/"key": "value"}',  # JavaScript comment
        b'{"key": "value",}',     # Trailing comma
        b'[1, 2, 3,]',           # Trailing comma in array
    ]
    
    for invalid_json in test_cases:
        mock_resp = MockResponse(200, invalid_json)
        response = Response(mock_resp)
        
        try:
            result = response.to_dict
            print(f"Unexpected success with invalid JSON: {invalid_json!r}, result: {result}")
        except json.JSONDecodeError:
            pass  # Expected


# Test 7: HTTPError with various body types from real HTTP errors
def test_httperror_real_world_bodies():
    """Test HTTPError with body content similar to real HTTP errors"""
    test_cases = [
        (400, b'Bad Request'),  # Plain text
        (404, b'<!DOCTYPE html><html><body>404 Not Found</body></html>'),  # HTML
        (500, b'{"error": "Internal Server Error", "code": 500}'),  # JSON
        (503, b''),  # Empty body
        (502, b'\xFF\xFE'),  # Binary data (BOM marker)
    ]
    
    for status_code, body in test_cases:
        error = HTTPError(status_code, f"HTTP {status_code}", body, {})
        
        # Should preserve the body
        assert error.body == body
        assert error.status_code == status_code
        
        # to_dict should work only for valid JSON
        if body.startswith(b'{'):
            try:
                result = error.to_dict
                assert isinstance(result, dict)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass


# Test 8: Client with versioned URL edge cases
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
))
def test_client_version_types(version):
    """Test Client with various version types"""
    client = Client(host='http://test', version=version)
    
    # Should convert version to string
    url = client._build_url(None)
    assert f'/v{str(version)}' in url


# Test 9: Response with large status codes
@given(st.integers(min_value=-1000000, max_value=1000000))
def test_response_extreme_status_codes(status_code):
    """Test Response with extreme status code values"""
    mock_resp = MockResponse(status_code, b'test')
    response = Response(mock_resp)
    
    # Should preserve any integer status code
    assert response.status_code == status_code


# Test 10: Client timeout edge cases
@given(st.one_of(
    st.none(),
    st.floats(min_value=-10, max_value=1000),
    st.integers(min_value=-10, max_value=1000)
))
def test_client_timeout_values(timeout):
    """Test Client with various timeout values"""
    try:
        client = Client(host='http://test', timeout=timeout)
        assert client.timeout == timeout
        
        # Child clients should inherit timeout
        child = client._('segment')
        assert child.timeout == timeout
    except Exception as e:
        # Negative timeouts might be rejected
        if timeout is not None and timeout < 0:
            pass  # Expected for negative timeouts
        else:
            print(f"Unexpected error with timeout {timeout}: {e}")


if __name__ == '__main__':
    print("Running request body bug tests...")
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])