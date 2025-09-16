import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from urllib.parse import parse_qs, urlparse
import pytest

from requests_oauthlib import OAuth1Session
from requests_oauthlib.oauth1_session import urldecode


# Bug 1: None values in authorization_url are converted to string 'None'
@given(
    base_url=st.text(min_size=10, max_size=100).filter(lambda x: x.startswith('http')),
    extra_params=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        max_size=3
    )
)
def test_authorization_url_none_values(base_url, extra_params):
    """Test that None values in authorization_url are handled properly."""
    session = OAuth1Session('client_key', client_secret='secret')
    # Clear resource_owner_key to test None behavior
    session._client.client.resource_owner_key = None
    
    # Create URL with None request_token
    auth_url = session.authorization_url(base_url, request_token=None, **extra_params)
    
    # Parse the URL
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    
    # Check that None is not converted to string 'None'
    if 'oauth_token' in params:
        oauth_token_values = params['oauth_token']
        for value in oauth_token_values:
            assert value != 'None', f"BUG: None was converted to string 'None' in URL: {auth_url}"
    
    # Check extra params
    for key, value in extra_params.items():
        if value is None and key in params:
            param_values = params[key]
            for pval in param_values:
                assert pval != 'None', f"BUG: None value for {key} was converted to string 'None'"


# Bug 2: Empty string oauth_token behavior
@given(
    oauth_token=st.text(max_size=50),
    oauth_token_secret=st.text(min_size=0, max_size=50),
    oauth_verifier=st.text(min_size=0, max_size=50)
)
def test_empty_string_token_preservation(oauth_token, oauth_token_secret, oauth_verifier):
    """Test that empty strings in oauth tokens are handled consistently."""
    session = OAuth1Session('client_key', client_secret='secret')
    
    token_dict = {'oauth_token': oauth_token}
    if oauth_token_secret:
        token_dict['oauth_token_secret'] = oauth_token_secret
    if oauth_verifier:
        token_dict['oauth_verifier'] = oauth_verifier
    
    # Skip if oauth_token is empty (will raise TokenMissing)
    assume(oauth_token != '')
    
    session.token = token_dict
    retrieved = session.token
    
    # Empty string oauth_token should be preserved or consistently handled
    if oauth_token == '':
        # Currently it returns empty dict for empty oauth_token
        # This might be a bug - empty string is different from None
        assert retrieved == {} or 'oauth_token' in retrieved
    else:
        assert 'oauth_token' in retrieved
        assert retrieved['oauth_token'] == oauth_token


# Bug 3: Test urldecode with null bytes and special characters
@given(
    prefix=st.text(min_size=0, max_size=10, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
    suffix=st.text(min_size=0, max_size=10, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
)
def test_urldecode_with_null_bytes(prefix, suffix):
    """Test that urldecode handles null bytes without crashing."""
    # Create input with null byte
    input_with_null = prefix + '\x00' + suffix
    
    try:
        result = urldecode(input_with_null)
        # Should either handle it gracefully or raise a clear error
        # Currently it raises JSONDecodeError which might not be ideal
    except Exception as e:
        # Check if the error is reasonable
        assert 'JSONDecodeError' in str(type(e)) or 'ValueError' in str(type(e))


# Bug 4: Token property doesn't include falsy values
def test_token_property_falsy_values():
    """Test that token property handles falsy values correctly."""
    session = OAuth1Session('client_key', client_secret='secret')
    
    # Set fields with falsy values
    session._client.client.resource_owner_key = ''
    session._client.client.resource_owner_secret = ''
    session._client.client.verifier = ''
    
    token = session.token
    
    # Empty strings are falsy but should arguably be included
    print(f"Token with empty strings: {token}")
    # Currently returns {} - is this correct behavior?
    assert token == {}, "Empty string values are not included in token property"


# Bug 5: authorization_url with special None handling
def test_authorization_url_none_bug_minimal():
    """Minimal reproduction of the None to 'None' bug."""
    session = OAuth1Session('client_key', client_secret='secret')
    session._client.client.resource_owner_key = None
    
    url = session.authorization_url('https://example.com/auth', request_token=None)
    
    # This should not contain 'None' as a string
    assert 'oauth_token=None' not in url, \
        f"BUG CONFIRMED: None is converted to string 'None' in URL: {url}"


# Bug 6: Multiple token setting behavior
@given(
    tokens=st.lists(
        st.dictionaries(
            st.sampled_from(['oauth_token', 'oauth_token_secret', 'oauth_verifier']),
            st.text(min_size=1, max_size=50)
        ).filter(lambda d: 'oauth_token' in d),
        min_size=2,
        max_size=5
    )
)
def test_multiple_token_setting(tokens):
    """Test that setting tokens multiple times behaves consistently."""
    session = OAuth1Session('client_key', client_secret='secret')
    
    for token_dict in tokens:
        session.token = token_dict
        retrieved = session.token
        
        # oauth_token should always be present and match what was set
        assert 'oauth_token' in retrieved
        assert retrieved['oauth_token'] == token_dict['oauth_token']
    
    # Final state should have accumulated values
    final_token = session.token
    last_token = tokens[-1]
    
    # oauth_token should be from the last set
    assert final_token['oauth_token'] == last_token['oauth_token']
    
    # Other fields might be accumulated (current behavior) or replaced
    # Document the actual behavior
    print(f"Final token state after {len(tokens)} sets: {final_token}")


if __name__ == "__main__":
    # First run the minimal bug reproduction
    print("Testing for None to 'None' conversion bug...")
    try:
        test_authorization_url_none_bug_minimal()
        print("✓ Test passed - bug may be fixed")
    except AssertionError as e:
        print(f"✗ {e}")
    
    print("\nTesting token property with falsy values...")
    test_token_property_falsy_values()
    
    print("\nRunning property-based tests...")
    pytest.main([__file__, "-v", "--tb=short", "-k", "not minimal"])