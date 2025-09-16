#!/usr/bin/env python3
"""More sophisticated property-based tests for python_http_client edge cases"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
import math

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


class MockHTTPError:
    """Mock HTTP error for testing HTTPError class"""
    def __init__(self, code, reason, body, headers=None):
        self.code = code
        self.reason = reason
        self._body = body
        self.hdrs = headers or {}
    
    def read(self):
        return self._body


# Test 1: Response.to_dict with invalid JSON should raise proper error
@given(st.binary().filter(lambda x: x and not x.strip().startswith(b'{')))
def test_response_to_dict_invalid_json(invalid_json):
    """Test that Response.to_dict raises appropriate error for invalid JSON"""
    mock_resp = MockResponse(200, invalid_json)
    response = Response(mock_resp)
    
    try:
        result = response.to_dict
        # If it doesn't raise an error, check if result is reasonable
        print(f"Unexpected success with input: {invalid_json!r}, result: {result}")
    except json.JSONDecodeError:
        pass  # Expected behavior
    except UnicodeDecodeError:
        pass  # Also acceptable for binary data


# Test 2: HTTPError.to_dict with invalid JSON should raise proper error
@given(
    st.integers(min_value=400, max_value=599),
    st.text(),
    st.binary().filter(lambda x: x and not x.strip().startswith(b'{'))
)
def test_httperror_to_dict_invalid_json(status_code, reason, invalid_json):
    """Test that HTTPError.to_dict raises appropriate error for invalid JSON"""
    mock_err = MockHTTPError(status_code, reason, invalid_json)
    error = HTTPError(mock_err)
    
    try:
        result = error.to_dict
        print(f"Unexpected success with input: {invalid_json!r}, result: {result}")
    except json.JSONDecodeError:
        pass  # Expected behavior
    except UnicodeDecodeError:
        pass  # Also acceptable for binary data


# Test 3: Client with special method names as segments
@given(st.sampled_from(['get', 'post', 'put', 'delete', 'patch']))
def test_client_method_name_as_segment(method_name):
    """Test that HTTP method names can't be used as URL segments via attribute access"""
    client = Client(host='http://test')
    
    # Accessing a method name should return a callable
    attr = getattr(client, method_name)
    assert callable(attr)
    
    # It should not add to the URL path
    assert method_name not in client._url_path


# Test 4: Client with 'version' as segment
def test_client_version_special_handling():
    """Test that 'version' has special handling"""
    client = Client(host='http://test')
    
    # Accessing 'version' should return a callable
    version_attr = client.version
    assert callable(version_attr)
    
    # Calling it should set the version
    new_client = version_attr(3)
    assert new_client._version == 3


# Test 5: Response.to_dict with JSON containing special float values
def test_response_json_special_floats():
    """Test Response.to_dict with JSON containing NaN, Infinity"""
    # JSON doesn't support NaN or Infinity by default
    test_cases = [
        b'{"value": NaN}',
        b'{"value": Infinity}',
        b'{"value": -Infinity}',
        b'{"value": null}',  # This should work
    ]
    
    for json_bytes in test_cases:
        mock_resp = MockResponse(200, json_bytes)
        response = Response(mock_resp)
        
        try:
            result = response.to_dict
            if json_bytes == b'{"value": null}':
                assert result == {"value": None}
            else:
                print(f"Unexpected success with: {json_bytes}, result: {result}")
        except json.JSONDecodeError:
            if json_bytes == b'{"value": null}':
                print(f"Unexpected failure with valid JSON: {json_bytes}")


# Test 6: Client URL building with empty segments
@given(st.lists(st.text(), min_size=1, max_size=5))
def test_client_url_with_empty_segments(segments):
    """Test URL building with potentially empty segments"""
    client = Client(host='http://test', url_path=segments)
    url = client._build_url(None)
    
    # Empty segments should create double slashes
    for i, segment in enumerate(segments):
        if segment == '':
            # Empty segment creates //
            assert '//' in url or url.endswith('/')
            

# Test 7: Client URL building with Unicode characters
@given(
    st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψω', min_size=1, max_size=10),
    st.dictionaries(
        st.text(alphabet='абвгдеёжзийклмнопрстуфхцчшщъыьэюя', min_size=1, max_size=5),
        st.text(alphabet='你好世界', min_size=1, max_size=5),
        min_size=1,
        max_size=3
    )
)
def test_client_unicode_handling(greek_segment, cyrillic_chinese_params):
    """Test that Client handles Unicode properly in URLs"""
    client = Client(host='http://test')
    child = client._(greek_segment)
    
    # Should be able to build URL with Unicode
    url = child._build_url(cyrillic_chinese_params)
    
    # URL should contain encoded versions
    assert 'http://test' in url
    assert '?' in url  # Should have query params


# Test 8: Client._build_url with None vs empty dict query params
def test_client_build_url_none_vs_empty_params():
    """Test difference between None and empty dict for query params"""
    client = Client(host='http://test', url_path=['api'])
    
    url_none = client._build_url(None)
    url_empty = client._build_url({})
    
    # Both should produce the same URL without query string
    assert url_none == url_empty
    assert '?' not in url_none
    assert '?' not in url_empty


# Test 9: Response body as non-UTF8 bytes
@given(st.binary(min_size=1))
def test_response_non_utf8_body(binary_data):
    """Test Response with non-UTF8 binary data"""
    mock_resp = MockResponse(200, binary_data)
    response = Response(mock_resp)
    
    # body property should return raw bytes
    assert response.body == binary_data
    
    # to_dict should handle decode errors
    if binary_data:
        try:
            result = response.to_dict
            # If successful, it should have decoded as UTF-8 and parsed as JSON
            assert isinstance(result, (dict, list, str, int, float, type(None)))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass  # Expected for non-JSON or non-UTF8 data


# Test 10: Large nested JSON structures
@settings(max_examples=10)
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=100),
            st.dictionaries(st.text(max_size=20), children, max_size=50)
        ),
        max_leaves=1000
    )
)
def test_response_large_json_structures(data):
    """Test Response.to_dict with large nested JSON structures"""
    json_bytes = json.dumps(data).encode('utf-8')
    mock_resp = MockResponse(200, json_bytes)
    response = Response(mock_resp)
    
    # Should handle large structures
    assert response.to_dict == data


# Test 11: Client request_body handling for different content types
def test_client_request_body_content_type_handling():
    """Test how Client handles request_body with different Content-Type headers"""
    # This tests the actual HTTP request building logic
    client = Client(host='http://test')
    
    # Test 1: With JSON content type (default)
    client1 = Client(host='http://test')
    # We can't easily test the actual HTTP call, but we can test the header setting
    assert 'Content-Type' not in client1.request_headers
    
    # Test 2: With non-JSON content type
    client2 = Client(host='http://test', request_headers={'Content-Type': 'text/plain'})
    assert client2.request_headers['Content-Type'] == 'text/plain'
    
    # Test 3: Content-Type preservation during updates
    client3 = Client(host='http://test')
    client3._update_headers({'Content-Type': 'application/xml'})
    assert client3.request_headers['Content-Type'] == 'application/xml'


if __name__ == '__main__':
    print("Running edge case tests for python_http_client...")
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])