import base64
import warnings
from hypothesis import given, strategies as st, assume
import requests.auth


@given(
    st.text(min_size=1), 
    st.text(min_size=1)
)
def test_httpbasicauth_equality_reflexive(username, password):
    """Test that HTTPBasicAuth is equal to itself (reflexivity)"""
    auth = requests.auth.HTTPBasicAuth(username, password)
    assert auth == auth
    assert not (auth != auth)


@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_httpbasicauth_equality_symmetric(user1, pass1, user2, pass2):
    """Test that HTTPBasicAuth equality is symmetric"""
    auth1 = requests.auth.HTTPBasicAuth(user1, pass1)
    auth2 = requests.auth.HTTPBasicAuth(user2, pass2)
    
    # If auth1 == auth2, then auth2 == auth1
    if auth1 == auth2:
        assert auth2 == auth1
    
    # If auth1 != auth2, then auth2 != auth1
    if auth1 != auth2:
        assert auth2 != auth1


@given(
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_httpbasicauth_ne_is_not_eq(username, password):
    """Test that __ne__ is properly implemented as not __eq__"""
    auth1 = requests.auth.HTTPBasicAuth(username, password)
    auth2 = requests.auth.HTTPBasicAuth(username, password)
    auth3 = requests.auth.HTTPBasicAuth(username + "x", password)
    
    # Same auth objects
    assert (auth1 != auth2) == (not (auth1 == auth2))
    # Different auth objects
    assert (auth1 != auth3) == (not (auth1 == auth3))


@given(
    st.text(min_size=1).filter(lambda x: '\x00' not in x),
    st.text(min_size=1).filter(lambda x: '\x00' not in x)
)
def test_basic_auth_str_format(username, password):
    """Test that _basic_auth_str produces correct format"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        auth_str = requests.auth._basic_auth_str(username, password)
    
    # Should start with "Basic "
    assert auth_str.startswith("Basic ")
    
    # The part after "Basic " should be valid base64
    encoded_part = auth_str[6:]  # Skip "Basic "
    try:
        decoded = base64.b64decode(encoded_part)
        # Should decode to username:password format
        expected = f"{username}:{password}".encode('latin1')
        assert decoded == expected
    except Exception as e:
        # If decoding fails, the property is violated
        raise AssertionError(f"Failed to decode base64: {e}")


@given(
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none()
    ),
    st.text(min_size=1)
)
def test_basic_auth_str_non_string_username(non_string_username, password):
    """Test that _basic_auth_str handles non-string usernames"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        auth_str = requests.auth._basic_auth_str(non_string_username, password)
        
        # Should produce a warning for non-string username
        assert len(w) > 0
        assert any("Non-string usernames" in str(warning.message) for warning in w)
        
        # Should still produce valid auth string
        assert auth_str.startswith("Basic ")


@given(
    st.text(min_size=1),
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none()
    )
)
def test_basic_auth_str_non_string_password(username, non_string_password):
    """Test that _basic_auth_str handles non-string passwords"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        auth_str = requests.auth._basic_auth_str(username, non_string_password)
        
        # Should produce a warning for non-string password
        assert len(w) > 0
        assert any("Non-string passwords" in str(warning.message) for warning in w)
        
        # Should still produce valid auth string
        assert auth_str.startswith("Basic ")


@given(
    st.text(min_size=1).filter(lambda x: '\x00' not in x),
    st.text(min_size=1).filter(lambda x: '\x00' not in x)
)
def test_basic_auth_round_trip(username, password):
    """Test encoding and decoding round-trip for basic auth"""
    # First encode
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        auth_str = requests.auth._basic_auth_str(username, password)
    
    # Extract the base64 part
    encoded_part = auth_str[6:]  # Skip "Basic "
    
    # Decode it
    decoded = base64.b64decode(encoded_part).decode('latin1')
    
    # Should get back username:password
    assert decoded == f"{username}:{password}"


@given(
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_httpdigestauth_initialization(username, password):
    """Test HTTPDigestAuth can be initialized and has expected attributes"""
    auth = requests.auth.HTTPDigestAuth(username, password)
    
    assert auth.username == username
    assert auth.password == password
    
    # Should have the public methods we discovered
    assert hasattr(auth, 'build_digest_header')
    assert hasattr(auth, 'handle_401')
    assert hasattr(auth, 'handle_redirect')
    assert hasattr(auth, 'init_per_thread_state')


@given(
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_httpproxyauth_inherits_basic(username, password):
    """Test that HTTPProxyAuth properly inherits from HTTPBasicAuth"""
    proxy_auth = requests.auth.HTTPProxyAuth(username, password)
    basic_auth = requests.auth.HTTPBasicAuth(username, password)
    
    # HTTPProxyAuth should be an instance of HTTPBasicAuth
    assert isinstance(proxy_auth, requests.auth.HTTPBasicAuth)
    
    # Should have same username and password
    assert proxy_auth.username == basic_auth.username
    assert proxy_auth.password == basic_auth.password