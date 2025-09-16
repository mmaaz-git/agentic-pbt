import json
import pickle
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import python_http_client.client as client
import python_http_client.exceptions as exceptions


@given(
    st.lists(st.text(min_size=1).filter(lambda x: '/' not in x), min_size=0, max_size=10),
    st.booleans(),
    st.dictionaries(st.text(min_size=1), st.text(), min_size=0, max_size=5),
    st.text(),
    st.one_of(st.none(), st.integers(min_value=1, max_value=10))
)
def test_client_url_building(url_segments, append_slash, query_params, host, version):
    """Test that URL building preserves structure and handles query params correctly"""
    c = client.Client(
        host=host,
        url_path=url_segments,
        append_slash=append_slash,
        version=version
    )
    
    url = c._build_url(query_params)
    
    # Property 1: URL should contain the host
    assert host in url
    
    # Property 2: If append_slash is True and there are segments, URL should end with / (before query params)
    if append_slash and url_segments:
        if query_params:
            # Check the part before the query string
            url_without_query = url.split('?')[0]
            assert url_without_query.endswith('/')
        else:
            assert url.endswith('/')
    
    # Property 3: All URL segments should appear in order
    for segment in url_segments:
        assert segment in url
    
    # Property 4: Query parameters should be in the URL if provided
    if query_params:
        assert '?' in url
        for key in query_params:
            assert key in url


@given(st.binary())
def test_response_to_dict_with_json_body(body_bytes):
    """Test Response.to_dict handles various body contents"""
    # Create a mock response object
    class MockResponse:
        def getcode(self):
            return 200
        def read(self):
            return body_bytes
        def info(self):
            return {}
    
    resp = client.Response(MockResponse())
    
    # Try to decode as JSON
    try:
        result = resp.to_dict
        if body_bytes:
            # If we got here, it should have successfully decoded
            # Verify it's valid JSON by encoding back
            json.dumps(result)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # This is expected for non-JSON/non-UTF8 bodies
        pass


@given(st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.floats(allow_nan=False), st.booleans(), st.none())))
def test_response_json_round_trip(data):
    """Test that Response.to_dict can decode what json.dumps encodes"""
    json_bytes = json.dumps(data).encode('utf-8')
    
    class MockResponse:
        def getcode(self):
            return 200
        def read(self):
            return json_bytes
        def info(self):
            return {}
    
    resp = client.Response(MockResponse())
    result = resp.to_dict
    
    # Property: decode(encode(x)) == x
    assert result == data


@given(
    st.integers(min_value=100, max_value=599),
    st.text(),
    st.binary(),
    st.dictionaries(st.text(), st.text())
)
def test_http_error_initialization_and_pickling(status_code, reason, body, headers):
    """Test HTTPError can be initialized and pickled/unpickled"""
    # Test 4-arg initialization
    err = exceptions.HTTPError(status_code, reason, body, headers)
    
    assert err.status_code == status_code
    assert err.reason == reason
    assert err.body == body
    assert err.headers == headers
    
    # Test pickling round-trip
    pickled = pickle.dumps(err)
    unpickled = pickle.loads(pickled)
    
    assert unpickled.status_code == status_code
    assert unpickled.reason == reason
    assert unpickled.body == body
    assert unpickled.headers == headers


@given(
    st.text(),
    st.dictionaries(st.text(), st.text()),
    st.one_of(st.none(), st.integers(min_value=1, max_value=10)),
    st.lists(st.text()),
    st.booleans(),
    st.one_of(st.none(), st.floats(min_value=0.1, max_value=60))
)
def test_client_state_serialization(host, headers, version, url_path, append_slash, timeout):
    """Test Client can be pickled and unpickled preserving state"""
    c = client.Client(
        host=host,
        request_headers=headers,
        version=version,
        url_path=url_path,
        append_slash=append_slash,
        timeout=timeout
    )
    
    # Pickle and unpickle
    pickled = pickle.dumps(c)
    restored = pickle.loads(pickled)
    
    # All attributes should be preserved
    assert restored.host == host
    assert restored.request_headers == headers
    assert restored._version == version
    assert restored._url_path == url_path
    assert restored.append_slash == append_slash
    assert restored.timeout == timeout


@given(st.integers(min_value=100, max_value=599))
def test_handle_error_mapping(error_code):
    """Test that handle_error maps error codes to correct exception types"""
    class MockHTTPError:
        def __init__(self, code):
            self.code = code
            self.reason = "Test reason"
            self.hdrs = {}
        def read(self):
            return b"Test body"
    
    mock_err = MockHTTPError(error_code)
    result = exceptions.handle_error(mock_err)
    
    # Check that known error codes map to specific exception types
    if error_code in exceptions.err_dict:
        assert isinstance(result, exceptions.err_dict[error_code])
        assert result.status_code == error_code
    else:
        # Unknown error codes should return base HTTPError
        assert isinstance(result, exceptions.HTTPError)
        assert result.status_code == error_code


@given(st.lists(st.text(min_size=1).filter(lambda s: s not in client.Client.methods)))
def test_client_dynamic_url_building(segments):
    """Test that Client builds URLs dynamically through attribute access"""
    c = client.Client(host="http://example.com")
    
    # Build client by chaining attribute access
    current = c
    for segment in segments:
        current = getattr(current, segment)
    
    # The URL path should contain all segments
    assert current._url_path == segments


@given(st.sampled_from(['get', 'post', 'put', 'patch', 'delete']))
def test_client_recognizes_http_methods(method):
    """Test that Client recognizes HTTP method names"""
    c = client.Client(host="http://example.com")
    
    # Getting a method attribute should return a callable
    method_func = getattr(c, method)
    assert callable(method_func)
    
    # It should not add the method name to the URL path
    assert method not in c._url_path