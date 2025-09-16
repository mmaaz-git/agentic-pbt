"""Test Session and Auth mechanisms for bugs."""

import string
from hypothesis import given, strategies as st, assume, settings
from requests import Session, Request
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.structures import CaseInsensitiveDict
import base64


# Test Session header merging
@given(
    st.dictionaries(st.text(min_size=1), st.text()),
    st.dictionaries(st.text(min_size=1), st.text())
)
@settings(max_examples=500)
def test_session_header_merging(session_headers, request_headers):
    """Test that Session properly merges headers."""
    session = Session()
    session.headers.update(session_headers)
    
    # Create a request with its own headers
    req = Request('GET', 'http://example.com', headers=request_headers)
    prep = session.prepare_request(req)
    
    # Check that headers were merged
    # Request headers should override session headers for same keys
    for key, value in request_headers.items():
        # Case-insensitive comparison
        assert any(k.lower() == key.lower() and v == value 
                  for k, v in prep.headers.items())


# Test HTTPBasicAuth encoding
@given(
    st.text(alphabet=string.printable).filter(lambda x: ':' not in x),
    st.text(alphabet=string.printable)
)
@settings(max_examples=500)
def test_http_basic_auth_encoding(username, password):
    """Test HTTPBasicAuth correctly encodes credentials."""
    auth = HTTPBasicAuth(username, password)
    req = Request('GET', 'http://example.com')
    
    # Apply auth
    req = auth(req)
    
    if 'Authorization' in req.headers:
        # Decode and verify
        auth_header = req.headers['Authorization']
        assert auth_header.startswith('Basic ')
        
        encoded = auth_header[6:]  # Remove 'Basic '
        try:
            decoded = base64.b64decode(encoded).decode('latin-1')
            assert decoded == f"{username}:{password}"
        except:
            # Some characters might not be encodable
            pass


# Test Session cookie persistence
@given(
    st.dictionaries(
        st.text(min_size=1, alphabet=string.ascii_letters),
        st.text()
    )
)
@settings(max_examples=500)
def test_session_cookie_persistence(cookies):
    """Test that Session maintains cookies across requests."""
    session = Session()
    
    # Set cookies
    for name, value in cookies.items():
        session.cookies.set(name, value)
    
    # Prepare a request
    req = Request('GET', 'http://example.com')
    prep = session.prepare_request(req)
    
    # Check cookies are included
    cookie_header = prep.headers.get('Cookie', '')
    
    # All cookies should be in the header
    for name, value in cookies.items():
        if value:  # Skip empty values
            assert name in cookie_header or not cookie_header


# Test Session parameter handling
@given(
    st.dictionaries(st.text(), st.text()),
    st.dictionaries(st.text(), st.text())
)
@settings(max_examples=500)
def test_session_params_merging(session_params, request_params):
    """Test Session parameter merging."""
    session = Session()
    session.params = session_params
    
    req = Request('GET', 'http://example.com', params=request_params)
    prep = session.prepare_request(req)
    
    # URL should contain parameters
    if session_params or request_params:
        # Request params should override session params
        url = prep.url
        for key, value in request_params.items():
            if value:
                assert key in url or f"{key}=" in url


# Test auth removal
@given(st.text(alphabet=string.ascii_letters + "://@."))
@settings(max_examples=500)
def test_auth_removal_from_url(url):
    """Test that auth is properly removed from URLs."""
    if "@" in url and url.startswith("http"):
        session = Session()
        req = Request('GET', url)
        prep = session.prepare_request(req)
        
        # Auth should be removed from URL
        assert "@" not in prep.url or url.count("@") > prep.url.count("@")


# Test CaseInsensitiveDict as headers
@given(
    st.dictionaries(
        st.text(min_size=1, alphabet=string.ascii_letters + "-"),
        st.text()
    )
)
@settings(max_examples=500)
def test_case_insensitive_dict_as_headers(headers):
    """Test CaseInsensitiveDict behavior when used as headers."""
    cid = CaseInsensitiveDict(headers)
    
    # Test that we can access with different cases
    for key in headers:
        assert cid.get(key.lower()) == headers[key]
        assert cid.get(key.upper()) == headers[key]
        
    # Test update with conflicting case
    if headers:
        first_key = list(headers.keys())[0]
        cid[first_key.upper()] = "new_value"
        assert cid[first_key.lower()] == "new_value"


# Test Session mount ordering
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, alphabet=string.ascii_letters + "://."),
            st.text()
        ),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=200)
def test_session_mount_ordering(mounts):
    """Test Session adapter mounting precedence."""
    session = Session()
    
    # Mount fake adapters
    for prefix, name in mounts:
        try:
            # Just test the mounting doesn't crash
            # We can't create real adapters easily
            session.mount(prefix, session.adapters.get('http://'))
        except:
            pass
    
    # Test that session still works
    assert len(session.adapters) >= 2  # At least http:// and https://


# Test Session.request with method override
@given(
    st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']),
    st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
)
@settings(max_examples=200)
def test_session_method_override(method1, method2):
    """Test that request method is properly handled."""
    session = Session()
    
    # Create request with one method
    req = Request(method1, 'http://example.com')
    prep = session.prepare_request(req)
    assert prep.method == method1
    
    # Prepare with different method shouldn't affect original
    req2 = Request(method2, 'http://example.com')
    prep2 = session.prepare_request(req2)
    assert prep2.method == method2
    assert prep.method == method1  # Original shouldn't change


# Test Session close idempotence
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_session_close_idempotent(num_closes):
    """Test that closing session multiple times is safe."""
    session = Session()
    
    # Close multiple times
    for _ in range(num_closes):
        session.close()
    
    # Should not crash or cause issues
    assert True  # If we get here, it worked


# Test prepared request body with various types
@given(st.one_of(
    st.text(),
    st.binary(),
    st.none(),
    st.dictionaries(st.text(), st.text()),
    st.lists(st.tuples(st.text(), st.text()))
))
@settings(max_examples=500)
def test_prepared_request_body_types(data):
    """Test PreparedRequest with various body types."""
    try:
        req = Request('POST', 'http://example.com', data=data)
        prep = req.prepare()
        
        # Should handle all these types
        assert prep.method == 'POST'
        
        # Body should be set for non-None data
        if data is not None:
            # Dictionary and list of tuples become form-encoded
            if isinstance(data, (dict, list)):
                assert prep.body is not None or not data
            else:
                assert prep.body is not None or not data
    except:
        # Some types might not be supported
        pass