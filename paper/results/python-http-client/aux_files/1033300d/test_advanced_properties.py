#!/usr/bin/env python3
"""Advanced property-based tests for python_http_client"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
from urllib.parse import parse_qs, urlparse
import pickle

sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client, Response
from python_http_client.exceptions import HTTPError, handle_error


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


# Test 1: handle_error function with various status codes
@given(st.integers(min_value=100, max_value=599))
def test_handle_error_status_codes(status_code):
    """Test that handle_error returns appropriate exception types"""
    mock_err = MockHTTPError(status_code, "Test reason", b"Test body")
    exc = handle_error(mock_err)
    
    # Should always return an HTTPError or subclass
    assert isinstance(exc, HTTPError)
    
    # Check specific error types
    error_map = {
        400: 'BadRequestsError',
        401: 'UnauthorizedError',
        403: 'ForbiddenError',
        404: 'NotFoundError',
        405: 'MethodNotAllowedError',
        413: 'PayloadTooLargeError',
        415: 'UnsupportedMediaTypeError',
        429: 'TooManyRequestsError',
        500: 'InternalServerError',
        503: 'ServiceUnavailableError',
        504: 'GatewayTimeoutError'
    }
    
    if status_code in error_map:
        assert exc.__class__.__name__ == error_map[status_code]
    else:
        assert exc.__class__.__name__ == 'HTTPError'


# Test 2: Query parameter ordering preservation
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10).filter(lambda x: not any(c in x for c in ['&', '=', '?'])),
            st.text(max_size=10).filter(lambda x: not any(c in x for c in ['&', '=', '?']))
        ),
        min_size=1,
        max_size=10
    )
)
def test_client_query_param_ordering(param_list):
    """Test if query parameters maintain consistent ordering"""
    # Convert list to dict (may have duplicates)
    params = dict(param_list)
    
    client = Client(host='http://test')
    url1 = client._build_url(params)
    url2 = client._build_url(params)
    
    # URLs should be identical (deterministic)
    assert url1 == url2
    
    # Parse and verify all params are present
    parsed = urlparse(url1)
    if parsed.query:
        parsed_params = parse_qs(parsed.query)
        for key, value in params.items():
            assert key in parsed_params
            # parse_qs returns lists
            assert value in parsed_params[key]


# Test 3: Client state isolation between instances
@given(
    st.dictionaries(st.text(min_size=1), st.text()),
    st.dictionaries(st.text(min_size=1), st.text())
)
def test_client_state_isolation(headers1, headers2):
    """Test that different Client instances don't share state"""
    client1 = Client(host='http://test1', request_headers=headers1.copy())
    client2 = Client(host='http://test2', request_headers=headers2.copy())
    
    # Modify client1's headers
    client1._update_headers({'X-Custom': 'value1'})
    
    # client2 should not be affected
    assert 'X-Custom' not in client2.request_headers
    
    # Original headers should be preserved
    for key in headers2:
        assert client2.request_headers.get(key) == headers2[key]


# Test 4: Client pickle/unpickle support
@given(
    st.text(min_size=1).filter(lambda x: '/' not in x and x.strip()),
    st.integers(min_value=1, max_value=99),
    st.dictionaries(st.text(min_size=1), st.text()),
    st.lists(st.text(min_size=1).filter(lambda x: '/' not in x), max_size=3),
    st.booleans(),
    st.one_of(st.none(), st.floats(min_value=0.1, max_value=60))
)
def test_client_pickle_roundtrip(host, version, headers, url_path, append_slash, timeout):
    """Test that Client can be pickled and unpickled"""
    if not host.startswith('http'):
        host = 'http://' + host
    
    client1 = Client(
        host=host,
        version=version,
        request_headers=headers.copy(),
        url_path=url_path,
        append_slash=append_slash,
        timeout=timeout
    )
    
    # Pickle and unpickle
    pickled = pickle.dumps(client1)
    client2 = pickle.loads(pickled)
    
    # All attributes should be preserved
    assert client2.host == client1.host
    assert client2._version == client1._version
    assert client2.request_headers == client1.request_headers
    assert client2._url_path == client1._url_path
    assert client2.append_slash == client1.append_slash
    assert client2.timeout == client1.timeout


# Test 5: HTTPError pickle/unpickle with edge cases
@given(
    st.integers(min_value=400, max_value=599),
    st.text(),
    st.one_of(
        st.binary(),
        st.text().map(lambda x: x.encode('utf-8'))
    ),
    st.dictionaries(st.text(), st.text())
)
def test_httperror_pickle_edge_cases(status_code, reason, body, headers):
    """Test HTTPError pickling with various body types"""
    error1 = HTTPError(status_code, reason, body, headers)
    
    # Pickle and unpickle
    pickled = pickle.dumps(error1)
    error2 = pickle.loads(pickled)
    
    # All attributes should be preserved
    assert error2.status_code == error1.status_code
    assert error2.reason == error1.reason
    assert error2.body == error1.body
    assert error2.headers == error1.headers


# Test 6: Response with None body
def test_response_none_body():
    """Test Response handling of None body"""
    mock_resp = MockResponse(204, None)  # 204 No Content
    
    try:
        response = Response(mock_resp)
        # Should handle None gracefully
        assert response.body is None or response.body == b''
        assert response.to_dict is None
    except Exception as e:
        print(f"Unexpected error with None body: {e}")


# Test 7: Client method chaining with special characters
@given(
    st.lists(
        st.text(alphabet='!@$%^*()[]{}|\\:";\'<>,~`', min_size=1, max_size=3),
        min_size=1,
        max_size=3
    )
)
def test_client_special_char_segments(segments):
    """Test Client with special characters in URL segments"""
    client = Client(host='http://test')
    
    # Build client with special character segments
    current = client
    for segment in segments:
        current = current._(segment)
    
    # Should have all segments in path
    assert len(current._url_path) == len(segments)
    for i, segment in enumerate(segments):
        assert current._url_path[i] == segment
    
    # Should be able to build URL
    url = current._build_url(None)
    assert url.startswith('http://test/')


# Test 8: Client with extremely long URL paths
@given(
    st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=10, max_size=50),
        min_size=10,
        max_size=20
    )
)
@settings(max_examples=5)
def test_client_long_url_paths(segments):
    """Test Client with very long URL paths"""
    client = Client(host='http://test', url_path=segments)
    url = client._build_url(None)
    
    # All segments should be in the URL
    for segment in segments:
        assert f'/{segment}' in url or url.endswith(f'/{segment}')
    
    # URL should be properly formed
    assert url.startswith('http://test/')
    
    # Count slashes - should be len(segments) + 2 (http:// counts as 2)
    slash_count = url.count('/')
    assert slash_count >= len(segments) + 2


# Test 9: Response status code edge cases
@given(st.integers())
def test_response_status_codes(status_code):
    """Test Response with various status codes including invalid ones"""
    mock_resp = MockResponse(status_code, b'test')
    response = Response(mock_resp)
    
    # Should preserve any status code
    assert response.status_code == status_code


# Test 10: Client with mixed segment access patterns
def test_client_mixed_access_patterns():
    """Test mixing attribute access and _() method for segments"""
    client = Client(host='http://test')
    
    # Mix different access patterns
    child1 = client.api  # Attribute access
    child2 = child1._('v2')  # _() method
    child3 = child2.users  # Attribute access again
    child4 = child3._('123')  # _() method for numeric-like segment
    
    # Should have all segments
    assert child4._url_path == ['api', 'v2', 'users', '123']
    
    # URL should be correct
    url = child4._build_url(None)
    assert url == 'http://test/api/v2/users/123'


# Test 11: Query parameters with list values (common in APIs)
def test_client_query_params_with_lists():
    """Test how Client handles list values in query parameters"""
    client = Client(host='http://test')
    
    # Some APIs expect repeated parameters for lists
    params = {
        'ids': ['1', '2', '3'],
        'name': 'test'
    }
    
    # The library uses urlencode with doseq=True (second parameter)
    url = client._build_url(params)
    
    # Should handle the list somehow
    assert 'ids' in url
    assert 'name=test' in url


if __name__ == '__main__':
    print("Running advanced property tests for python_http_client...")
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])