import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from urllib.parse import urlencode, quote
import json
import pytest

from requests_oauthlib import OAuth1Session
from requests_oauthlib.oauth1_session import urldecode


# Strategy for OAuth tokens
oauth_token_strategy = st.dictionaries(
    st.sampled_from(['oauth_token', 'oauth_token_secret', 'oauth_verifier']),
    st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
)


@given(token_dict=oauth_token_strategy)
def test_token_setter_getter_round_trip(token_dict):
    """Test that setting a token and getting it back preserves the data."""
    # Must have at least oauth_token for _populate_attributes to work
    assume('oauth_token' in token_dict)
    
    session = OAuth1Session('client_key', client_secret='secret')
    
    # Set the token
    session.token = token_dict
    
    # Get it back
    retrieved_token = session.token
    
    # Check that all items from original dict are in retrieved token
    for key, value in token_dict.items():
        assert key in retrieved_token
        assert retrieved_token[key] == value


@given(
    params=st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='&=')),
        st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
    )
)
def test_parse_authorization_response_preserves_parameters(params):
    """Test that parse_authorization_response correctly extracts URL parameters."""
    # Always include oauth_token as it's required
    params['oauth_token'] = 'test_token_123'
    
    # Build a URL with these parameters
    base_url = 'https://example.com/callback'
    query_string = urlencode(params)
    full_url = f"{base_url}?{query_string}"
    
    session = OAuth1Session('client_key', client_secret='secret')
    
    # Parse the URL
    parsed = session.parse_authorization_response(full_url)
    
    # Check that all parameters were extracted
    for key, value in params.items():
        assert key in parsed
        assert parsed[key] == value
    
    # Also check via the token property
    token = session.token
    for key in ['oauth_token', 'oauth_token_secret', 'oauth_verifier']:
        if key in params:
            assert key in token
            assert token[key] == params[key]


@given(
    base_url=st.just('https://api.example.com/authorize'),
    extra_params=st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='&=')),
        st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        max_size=5
    ),
    request_token=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
)
def test_authorization_url_adds_parameters(base_url, extra_params, request_token):
    """Test that authorization_url properly adds parameters to the URL."""
    session = OAuth1Session('client_key', client_secret='secret')
    
    # Create authorization URL with extra parameters
    auth_url = session.authorization_url(base_url, request_token=request_token, **extra_params)
    
    # The URL should contain the base URL
    assert base_url in auth_url
    
    # It should contain the oauth_token parameter
    assert 'oauth_token=' in auth_url
    assert quote(request_token, safe='') in auth_url or request_token in auth_url
    
    # All extra parameters should be in the URL
    for key, value in extra_params.items():
        assert f'{key}=' in auth_url
        # Value should be either URL-encoded or present as-is if no special chars
        assert quote(str(value), safe='') in auth_url or str(value) in auth_url


# Test urldecode with both URL-encoded and JSON data
@given(data=st.dictionaries(
    st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='&=')),
    st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
))
def test_urldecode_handles_urlencoded_data(data):
    """Test that urldecode correctly handles URL-encoded data."""
    # Create URL-encoded string
    encoded = urlencode(data)
    
    # Decode it
    result = urldecode(encoded)
    
    # Should get back the same data
    for key, value in data.items():
        assert key in result
        assert result[key][0] == value  # urldecode returns lists of values


@given(data=st.dictionaries(
    st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
    st.one_of(
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.none(),
        st.booleans()
    )
))
def test_urldecode_fallback_to_json(data):
    """Test that urldecode falls back to JSON parsing when URL decoding fails."""
    # Create JSON string
    json_str = json.dumps(data)
    
    # urldecode should fall back to JSON parsing
    result = urldecode(json_str)
    
    # Should get back the same data
    assert result == data


@given(
    client_key=st.text(min_size=1, max_size=50),
    client_secret=st.text(min_size=1, max_size=50),
    resource_owner_key=st.text(min_size=1, max_size=50),
    resource_owner_secret=st.text(min_size=1, max_size=50)
)
def test_authorized_property_consistency(client_key, client_secret, resource_owner_key, resource_owner_secret):
    """Test that the authorized property is consistent with the presence of credentials."""
    # Test with HMAC signature (default)
    session = OAuth1Session(client_key, client_secret=client_secret)
    
    # Initially not authorized (no resource owner credentials)
    assert session.authorized == False
    
    # Set resource owner credentials via token
    session.token = {
        'oauth_token': resource_owner_key,
        'oauth_token_secret': resource_owner_secret
    }
    
    # Now should be authorized (has all three: client_secret, resource_owner_key, resource_owner_secret)
    assert session.authorized == True
    
    # Remove resource_owner_secret
    session._client.client.resource_owner_secret = None
    assert session.authorized == False
    
    # Restore it but remove client_secret
    session._client.client.resource_owner_secret = resource_owner_secret
    session._client.client.client_secret = None
    assert session.authorized == False


@given(
    params=st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='&=\x00')),
        st.text(min_size=0, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        min_size=1
    )
)
def test_parse_authorization_response_token_round_trip(params):
    """Test round-trip: parse_authorization_response sets token, token getter retrieves it."""
    # Ensure oauth_token is present
    params['oauth_token'] = params.get('oauth_token', 'default_token')
    
    base_url = 'https://example.com/callback'
    query_string = urlencode(params)
    full_url = f"{base_url}?{query_string}"
    
    session = OAuth1Session('client_key', client_secret='secret')
    
    # Parse sets the token internally
    parsed_result = session.parse_authorization_response(full_url)
    
    # Get token via property
    token_from_property = session.token
    
    # Verify round-trip for oauth fields
    oauth_fields = ['oauth_token', 'oauth_token_secret', 'oauth_verifier']
    for field in oauth_fields:
        if field in params:
            assert field in token_from_property
            assert token_from_property[field] == params[field]
            assert parsed_result[field] == params[field]


if __name__ == "__main__":
    # Run with increased examples for more thorough testing
    settings.register_profile("thorough", max_examples=500)
    settings.load_profile("thorough")
    
    pytest.main([__file__, "-v"])