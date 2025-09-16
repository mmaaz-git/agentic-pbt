import json
import pickle
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import python_http_client.client as client
import python_http_client.exceptions as exceptions


@given(st.binary().filter(lambda b: b != b''))
def test_response_to_dict_empty_check(body_bytes):
    """Test Response.to_dict property for empty body handling"""
    class MockResponse:
        def getcode(self):
            return 200
        def read(self):
            return body_bytes
        def info(self):
            return {}
    
    resp = client.Response(MockResponse())
    
    # According to the code, to_dict should return None for empty body
    # but what about whitespace-only bodies?
    if not body_bytes:
        assert resp.to_dict is None
    else:
        try:
            result = resp.to_dict
            # If it succeeded, it should be valid JSON that was decoded
            if result is not None:
                # Should be able to re-encode it
                json.dumps(result)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Expected for non-JSON bodies
            pass


@given(st.binary())
def test_http_error_to_dict_non_json_body(body):
    """Test HTTPError.to_dict with non-JSON bodies"""
    err = exceptions.HTTPError(500, "Server Error", body, {})
    
    try:
        result = err.to_dict
        # If it succeeded, the body must have been valid JSON
        # Let's verify by re-encoding
        json.dumps(result)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # This is expected for non-JSON bodies
        pass


@given(st.lists(st.text(min_size=1), min_size=0, max_size=10))
def test_client_url_path_mutation(segments):
    """Test that Client._url_path doesn't get mutated unexpectedly"""
    c = client.Client(host="http://example.com")
    
    # Build a chain of clients
    current = c
    for segment in segments:
        new_client = current._(segment)
        # The original client's path should not change
        assert c._url_path == []
        # The new client should have the accumulated path
        current = new_client
    
    # Final client should have all segments
    assert current._url_path == segments


@given(
    st.text(),
    st.lists(st.text()),
    st.one_of(st.none(), st.integers())
)
def test_build_versioned_url_edge_cases(host, url_path, version):
    """Test version URL building with edge cases"""
    c = client.Client(host=host, url_path=url_path, version=version)
    
    if version is not None:
        # Test _build_versioned_url directly
        test_url = "/test"
        result = c._build_versioned_url(test_url)
        
        # Should contain the version number
        assert f'/v{version}' in result
        # Should contain the host
        assert host in result
        # Should contain the test URL
        assert 'test' in result


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
))
def test_response_to_dict_complex_json(data):
    """Test Response.to_dict with complex nested JSON structures"""
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
    
    # Property: Complex structures should round-trip correctly
    assert result == data


@given(st.text().filter(lambda s: s and s not in client.Client.methods))
def test_getattr_vs_underscore_method(segment):
    """Test that __getattr__ and _ method produce equivalent results"""
    c = client.Client(host="http://example.com")
    
    # Using __getattr__ (attribute access)
    client1 = getattr(c, segment)
    
    # Using _ method
    client2 = c._(segment)
    
    # Both should produce clients with the same URL path
    assert client1._url_path == client2._url_path
    assert client1._url_path == [segment]


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.booleans()
)
def test_append_slash_consistency(segments, append_slash):
    """Test that append_slash behaves consistently"""
    c = client.Client(
        host="http://example.com",
        url_path=segments,
        append_slash=append_slash
    )
    
    url = c._build_url(None)
    
    if append_slash:
        # URL should end with /
        assert url.endswith('/'), f"URL {url} should end with / when append_slash=True"
    else:
        # URL should not end with / 
        assert not url.endswith('/'), f"URL {url} should not end with / when append_slash=False"


# Test for potential integer overflow or type confusion with version
@given(
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none()
    )
)
def test_version_handling_type_safety(version):
    """Test that version parameter handles different types safely"""
    try:
        c = client.Client(
            host="http://example.com",
            version=version
        )
        
        if version is not None:
            # Build a URL to see if version is handled correctly
            url = c._build_url(None)
            # The version should be converted to string in the URL
            if version is not None:
                assert f'/v{str(version)}' in url
    except Exception as e:
        # Check if the exception makes sense for the input
        pass


@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_request_headers_persistence(headers):
    """Test that request headers persist correctly across operations"""
    c = client.Client(
        host="http://example.com",
        request_headers=headers.copy()
    )
    
    # Headers should be stored
    assert c.request_headers == headers
    
    # Creating a new client via _ should preserve headers
    new_client = c._("segment")
    assert new_client.request_headers == headers
    
    # Modifying new client's headers shouldn't affect original
    new_client._update_headers({"new": "header"})
    # Wait, the _update_headers modifies in place, let's check
    # Actually both clients share the same dict reference!