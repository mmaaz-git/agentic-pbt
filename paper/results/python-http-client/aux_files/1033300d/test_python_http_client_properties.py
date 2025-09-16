#!/usr/bin/env python3
"""Property-based tests for python_http_client using Hypothesis"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

# Add the package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client, Response
from python_http_client.exceptions import HTTPError


# Strategy for generating valid JSON-encodable data
json_data = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    lambda children: st.one_of(
        st.lists(children),
        st.dictionaries(st.text(), children)
    ),
    max_leaves=10
)


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


# Test 1: Response.to_dict should handle various JSON inputs
@given(json_data)
def test_response_to_dict_json_roundtrip(data):
    """Test that Response.to_dict properly decodes JSON data"""
    # Encode the data as JSON bytes
    json_bytes = json.dumps(data).encode('utf-8')
    mock_resp = MockResponse(200, json_bytes)
    response = Response(mock_resp)
    
    # The to_dict property should decode back to the original data
    assert response.to_dict == data


# Test 2: Response.to_dict with empty body
@given(st.integers(min_value=100, max_value=599))
def test_response_to_dict_empty_body(status_code):
    """Test that Response.to_dict returns None for empty body"""
    mock_resp = MockResponse(status_code, b'')
    response = Response(mock_resp)
    assert response.to_dict is None


# Test 3: HTTPError.to_dict should handle various JSON inputs
@given(
    st.integers(min_value=400, max_value=599),
    st.text(),
    json_data
)
def test_httperror_to_dict_json_roundtrip(status_code, reason, data):
    """Test that HTTPError.to_dict properly decodes JSON error data"""
    json_bytes = json.dumps(data).encode('utf-8')
    mock_err = MockHTTPError(status_code, reason, json_bytes)
    error = HTTPError(mock_err)
    
    # The to_dict property should decode back to the original data
    assert error.to_dict == data


# Test 4: HTTPError initialization with both formats
@given(
    st.integers(min_value=400, max_value=599),
    st.text(),
    st.binary()
)
def test_httperror_init_both_formats(status_code, reason, body):
    """Test HTTPError can be initialized with both argument formats"""
    # Test with MockHTTPError object
    mock_err = MockHTTPError(status_code, reason, body, {})
    error1 = HTTPError(mock_err)
    assert error1.status_code == status_code
    assert error1.reason == reason
    assert error1.body == body
    
    # Test with direct arguments
    error2 = HTTPError(status_code, reason, body, {})
    assert error2.status_code == status_code
    assert error2.reason == reason
    assert error2.body == body


# Test 5: HTTPError reduce/pickle roundtrip
@given(
    st.integers(min_value=400, max_value=599),
    st.text(),
    st.binary(),
    st.dictionaries(st.text(), st.text())
)
def test_httperror_reduce_roundtrip(status_code, reason, body, headers):
    """Test HTTPError can be pickled and unpickled correctly"""
    error1 = HTTPError(status_code, reason, body, headers)
    
    # Use __reduce__ to get the pickle representation
    cls, args = error1.__reduce__()
    
    # Reconstruct the error
    error2 = cls(*args)
    
    assert error2.status_code == error1.status_code
    assert error2.reason == error1.reason
    assert error2.body == error1.body
    assert error2.headers == error1.headers


# Test 6: Client URL building with path segments
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()),
    st.lists(st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()), min_size=0, max_size=5)
)
def test_client_url_building_path_segments(host, segments):
    """Test that Client correctly builds URLs with path segments"""
    # Ensure host starts with http
    if not host.startswith('http'):
        host = 'http://' + host
    
    client = Client(host=host, url_path=segments)
    url = client._build_url(None)
    
    # URL should contain all segments
    for segment in segments:
        assert '/' + segment in url
    
    # URL should start with host
    assert url.startswith(host)


# Test 7: Client URL building with query parameters
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()),
    st.dictionaries(
        st.text(min_size=1).filter(lambda x: not any(c in x for c in ['&', '=', '?'])),
        st.text().filter(lambda x: not any(c in x for c in ['&', '=', '?'])),
        min_size=1,
        max_size=5
    )
)
def test_client_url_building_query_params(host, params):
    """Test that Client correctly encodes query parameters"""
    if not host.startswith('http'):
        host = 'http://' + host
    
    client = Client(host=host)
    url = client._build_url(params)
    
    # URL should contain query string
    assert '?' in url
    
    # All parameter keys should be in the URL
    for key in params:
        assert key in url


# Test 8: Client versioning
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()),
    st.integers(min_value=1, max_value=99)
)
def test_client_versioning(host, version):
    """Test that Client correctly adds version to URLs"""
    if not host.startswith('http'):
        host = 'http://' + host
    
    client = Client(host=host, version=version)
    url = client._build_url(None)
    
    # URL should contain version
    assert f'/v{version}' in url


# Test 9: Client append_slash behavior
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()),
    st.booleans()
)
def test_client_append_slash(host, append_slash):
    """Test that Client correctly appends slash when configured"""
    if not host.startswith('http'):
        host = 'http://' + host
    
    client = Client(host=host, append_slash=append_slash, url_path=['test'])
    url = client._build_url(None)
    
    if append_slash:
        # Should end with slash before query params
        assert '/test/' in url or url.endswith('/test/')
    else:
        # Should not have trailing slash
        assert not url.rstrip('?').endswith('/')


# Test 10: Client header updates preserve existing headers
@given(
    st.dictionaries(st.text(min_size=1), st.text()),
    st.dictionaries(st.text(min_size=1), st.text())
)
def test_client_header_updates(initial_headers, new_headers):
    """Test that Client._update_headers preserves existing headers"""
    client = Client(host='http://test', request_headers=initial_headers.copy())
    original_headers = client.request_headers.copy()
    
    client._update_headers(new_headers)
    
    # All original headers should still be present (unless overwritten)
    for key in original_headers:
        assert key in client.request_headers
        if key not in new_headers:
            assert client.request_headers[key] == original_headers[key]
    
    # All new headers should be present
    for key, value in new_headers.items():
        assert client.request_headers[key] == value


# Test 11: Client._build_client preserves configuration
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()),
    st.integers(min_value=1, max_value=99),
    st.dictionaries(st.text(min_size=1), st.text()),
    st.booleans(),
    st.floats(min_value=0.1, max_value=60)
)
def test_client_build_client_preserves_config(host, version, headers, append_slash, timeout):
    """Test that _build_client preserves all configuration"""
    if not host.startswith('http'):
        host = 'http://' + host
    
    parent = Client(
        host=host,
        version=version,
        request_headers=headers.copy(),
        append_slash=append_slash,
        timeout=timeout
    )
    
    child = parent._build_client('segment')
    
    # Child should preserve all parent configuration
    assert child.host == parent.host
    assert child._version == parent._version
    assert child.request_headers == parent.request_headers
    assert child.append_slash == parent.append_slash
    assert child.timeout == parent.timeout
    
    # Child should have additional segment
    assert 'segment' in child._url_path
    assert len(child._url_path) == len(parent._url_path) + 1


# Test 12: Client dynamic attribute access creates proper clients
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip() and x not in Client.methods),
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip() and x not in Client.methods)
)
def test_client_dynamic_attribute_chaining(segment1, segment2):
    """Test that dynamic attribute access properly chains segments"""
    client = Client(host='http://test')
    
    # Access attributes dynamically
    child1 = getattr(client, segment1)
    child2 = getattr(child1, segment2)
    
    # Should have both segments in url_path
    assert segment1 in child2._url_path
    assert segment2 in child2._url_path
    assert child2._url_path.index(segment1) < child2._url_path.index(segment2)


if __name__ == '__main__':
    print("Running property-based tests for python_http_client...")
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])