import base64
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from hypothesis import given, strategies as st, assume, settings
import requests.auth as auth


@given(
    st.text(min_size=0, max_size=1000),
    st.text(min_size=0, max_size=1000)
)
def test_basic_auth_round_trip(username, password):
    """Test that basic auth encoding is reversible"""
    auth_str = auth._basic_auth_str(username, password)
    
    # Extract the base64 part
    assert auth_str.startswith("Basic ")
    b64_part = auth_str[6:]
    
    # Decode it
    decoded = base64.b64decode(b64_part)
    
    # Verify we can reconstruct the original (accounting for latin1 encoding)
    expected_username = username.encode('latin1', errors='replace').decode('latin1')
    expected_password = password.encode('latin1', errors='replace').decode('latin1')
    expected = f"{expected_username}:{expected_password}".encode('latin1')
    
    assert decoded == expected


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
def test_httpbasicauth_equality_reflexive(username, password):
    """Test that HTTPBasicAuth equality is reflexive"""
    auth1 = auth.HTTPBasicAuth(username, password)
    assert auth1 == auth1
    assert not (auth1 != auth1)


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
def test_httpbasicauth_equality_symmetric(username, password):
    """Test that HTTPBasicAuth equality is symmetric"""
    auth1 = auth.HTTPBasicAuth(username, password)
    auth2 = auth.HTTPBasicAuth(username, password)
    assert auth1 == auth2
    assert auth2 == auth1
    assert not (auth1 != auth2)
    assert not (auth2 != auth1)


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
def test_httpbasicauth_equality_transitive(u1, p1, u2, p2):
    """Test transitivity of equality"""
    auth1 = auth.HTTPBasicAuth(u1, p1)
    auth2 = auth.HTTPBasicAuth(u2, p2)
    auth3 = auth.HTTPBasicAuth(u1, p1)
    
    if auth1 == auth2 and auth2 == auth3:
        assert auth1 == auth3


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
def test_httpdigestauth_equality_reflexive(username, password):
    """Test that HTTPDigestAuth equality is reflexive"""
    auth1 = auth.HTTPDigestAuth(username, password)
    assert auth1 == auth1
    assert not (auth1 != auth1)


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
def test_httpdigestauth_thread_safety(username, password):
    """Test that HTTPDigestAuth maintains separate state per thread"""
    digest_auth = auth.HTTPDigestAuth(username, password)
    
    def init_and_check():
        digest_auth.init_per_thread_state()
        # Each thread should have its own nonce count
        initial_count = digest_auth._thread_local.nonce_count
        digest_auth._thread_local.nonce_count += 1
        return initial_count, digest_auth._thread_local.nonce_count
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: init_and_check(), range(10)))
    
    # All threads should start with nonce_count = 0
    for initial, after in results:
        assert initial == 0
        assert after == 1


@given(st.text(min_size=1, max_size=100))
def test_basic_auth_colon_in_username(username):
    """Test that colons in username don't break parsing"""
    assume(':' in username)
    password = "testpass"
    
    auth_str = auth._basic_auth_str(username, password)
    assert auth_str.startswith("Basic ")
    
    # The encoded value should still be decodable
    b64_part = auth_str[6:]
    decoded = base64.b64decode(b64_part).decode('latin1')
    
    # Should contain the username followed by a colon and the password
    # Even if username has colons, the format is username:password
    assert decoded == f"{username}:{password}"


@given(st.text(min_size=1, max_size=100))
def test_basic_auth_colon_in_password(password):
    """Test that colons in password are preserved"""
    assume(':' in password)
    username = "testuser"
    
    auth_str = auth._basic_auth_str(username, password)
    assert auth_str.startswith("Basic ")
    
    b64_part = auth_str[6:]
    decoded = base64.b64decode(b64_part).decode('latin1')
    
    # The first colon separates username from password
    # Additional colons in password should be preserved
    assert decoded == f"{username}:{password}"


@given(
    st.text(min_size=0, max_size=100).filter(lambda x: '\x00' not in x),
    st.text(min_size=0, max_size=100).filter(lambda x: '\x00' not in x)
)
def test_httpbasicauth_idempotent(username, password):
    """Test that applying HTTPBasicAuth multiple times is idempotent"""
    basic_auth = auth.HTTPBasicAuth(username, password)
    
    # Create a mock request object
    class MockRequest:
        def __init__(self):
            self.headers = {}
    
    request1 = MockRequest()
    request2 = MockRequest()
    
    # Apply auth once
    basic_auth(request1)
    auth_header1 = request1.headers.get('Authorization')
    
    # Apply auth again to same request
    basic_auth(request1)
    auth_header2 = request1.headers.get('Authorization')
    
    # Should produce the same result
    assert auth_header1 == auth_header2
    
    # And on a different request object
    basic_auth(request2)
    assert request2.headers.get('Authorization') == auth_header1


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
def test_httpproxyauth_vs_httpbasicauth(username, password):
    """Test that HTTPProxyAuth uses different header than HTTPBasicAuth"""
    basic_auth = auth.HTTPBasicAuth(username, password)
    proxy_auth = auth.HTTPProxyAuth(username, password)
    
    class MockRequest:
        def __init__(self):
            self.headers = {}
    
    request1 = MockRequest()
    request2 = MockRequest()
    
    basic_auth(request1)
    proxy_auth(request2)
    
    # Both should set headers
    assert 'Authorization' in request1.headers
    assert 'Proxy-Authorization' in request2.headers
    
    # The values should be the same (both use basic auth)
    assert request1.headers['Authorization'] == request2.headers['Proxy-Authorization']


@given(st.integers(min_value=0, max_value=1000000))
def test_digest_auth_nonce_counter_formatting(count):
    """Test that nonce counter is always formatted as 8 hex digits"""
    digest_auth = auth.HTTPDigestAuth("user", "pass")
    digest_auth.init_per_thread_state()
    digest_auth._thread_local.nonce_count = count
    
    # Format the nonce count as done in build_digest_header
    ncvalue = f"{digest_auth._thread_local.nonce_count:08x}"
    
    # Should always be 8 characters
    assert len(ncvalue) == 8
    # Should be valid hex
    assert all(c in '0123456789abcdef' for c in ncvalue)
    # Should convert back to original value
    assert int(ncvalue, 16) == count


@given(
    st.text(min_size=0, max_size=50),
    st.text(min_size=0, max_size=50)
)
def test_httpbasicauth_with_none_comparison(username, password):
    """Test equality comparison with None and other types"""
    auth1 = auth.HTTPBasicAuth(username, password)
    
    # Should not crash when comparing to None
    assert auth1 != None
    assert not (auth1 == None)
    
    # Should not crash when comparing to other types
    assert auth1 != "string"
    assert auth1 != 123
    assert auth1 != []
    assert not (auth1 == "string")


@given(
    st.text(alphabet=st.characters(blacklist_categories=['Cs']), min_size=0, max_size=100),
    st.text(alphabet=st.characters(blacklist_categories=['Cs']), min_size=0, max_size=100)
)
def test_basic_auth_unicode_handling(username, password):
    """Test that Unicode is properly handled in basic auth"""
    # This should not crash
    auth_str = auth._basic_auth_str(username, password)
    assert auth_str.startswith("Basic ")
    
    # The result should be a valid base64 string
    b64_part = auth_str[6:]
    try:
        decoded = base64.b64decode(b64_part)
        # Should be valid latin1 bytes
        decoded.decode('latin1')
    except Exception as e:
        raise AssertionError(f"Failed to decode auth string: {e}")


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
)
@settings(max_examples=100)
def test_digest_auth_handle_401_idempotent_for_non_401(username, password):
    """Test that handle_401 is idempotent for non-401 responses"""
    digest_auth = auth.HTTPDigestAuth(username, password)
    digest_auth.init_per_thread_state()
    
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.headers = {}
            self.is_redirect = False
    
    # Test various non-401 status codes
    for status_code in [200, 302, 404, 500]:
        response = MockResponse(status_code)
        
        # First call
        result1 = digest_auth.handle_401(response)
        count1 = digest_auth._thread_local.num_401_calls
        
        # Second call
        result2 = digest_auth.handle_401(response)
        count2 = digest_auth._thread_local.num_401_calls
        
        # Should return same response
        assert result1 is response
        assert result2 is response
        
        # Counter should be reset to 1 for non-4xx responses
        if not (400 <= status_code < 500):
            assert count1 == 1
            assert count2 == 1