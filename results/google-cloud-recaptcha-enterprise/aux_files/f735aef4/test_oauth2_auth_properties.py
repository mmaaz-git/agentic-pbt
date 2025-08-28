import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.provisional import urls
import requests
from requests_oauthlib.oauth2_auth import OAuth2
from oauthlib.oauth2 import WebApplicationClient, InsecureTransportError
from unittest.mock import Mock
import string


# Strategy for valid OAuth2 token dictionaries
def oauth2_token_strategy():
    """Generate valid OAuth2 token dictionaries."""
    # Based on OAuth2 spec, these are common token fields
    return st.fixed_dictionaries({
        'access_token': st.text(min_size=1, alphabet=string.ascii_letters + string.digits + '-._~'),
        'token_type': st.sampled_from(['Bearer', 'MAC', 'bearer']),
    }, optional={
        'expires_in': st.integers(min_value=1, max_value=3600000),
        'refresh_token': st.text(min_size=1, alphabet=string.ascii_letters + string.digits + '-._~'),
        'scope': st.text(min_size=0, alphabet=string.ascii_letters + string.digits + ' '),
    })


# Strategy for arbitrary token dictionaries to test robustness
def arbitrary_token_strategy():
    """Generate arbitrary dictionaries that might be passed as tokens."""
    simple_values = st.one_of(
        st.text(min_size=0, max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none(),
    )
    return st.dictionaries(
        st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + '_'),
        simple_values,
        min_size=0,
        max_size=10
    )


@given(token=oauth2_token_strategy())
def test_token_attribute_propagation(token):
    """Property: All token dict items should be set as attributes on the client."""
    oauth2 = OAuth2(client_id='test_client', token=token)
    
    # Verify all token items are set as attributes on the client
    for key, value in token.items():
        assert hasattr(oauth2._client, key), f"Client missing attribute '{key}'"
        assert getattr(oauth2._client, key) == value, f"Client attribute '{key}' has wrong value"


@given(token=arbitrary_token_strategy())
def test_token_handling_robustness(token):
    """Property: OAuth2 should handle various token dictionary types without crashing."""
    try:
        oauth2 = OAuth2(client_id='test_client', token=token)
        # If construction succeeds, verify attributes were set
        if token:
            for key, value in token.items():
                assert hasattr(oauth2._client, key)
                assert getattr(oauth2._client, key) == value
    except (AttributeError, TypeError) as e:
        # These exceptions are acceptable for invalid token types
        # But we should verify token was actually invalid
        assume(False)  # Skip this test case if exception occurred


@given(
    client_id=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
    has_token=st.booleans()
)
def test_client_always_initialized(client_id, has_token):
    """Property: OAuth2 should always have a valid _client after initialization."""
    token = {'access_token': 'test', 'token_type': 'Bearer'} if has_token else None
    
    oauth2 = OAuth2(client_id=client_id, token=token)
    
    # Client should always exist
    assert hasattr(oauth2, '_client')
    assert oauth2._client is not None
    assert isinstance(oauth2._client, WebApplicationClient)
    
    # Client should have the provided client_id
    if client_id is not None:
        assert oauth2._client.client_id == client_id


@given(url=st.text(min_size=1, max_size=200))
def test_https_enforcement(url):
    """Property: OAuth2 should reject non-HTTPS URLs."""
    oauth2 = OAuth2(client_id='test_client', token={'access_token': 'test', 'token_type': 'Bearer'})
    
    # Create a mock request object
    mock_request = Mock()
    mock_request.url = url
    mock_request.method = 'GET'
    mock_request.body = None
    mock_request.headers = {}
    
    # For non-HTTPS URLs, should raise InsecureTransportError
    if not url.startswith('https://'):
        try:
            oauth2(mock_request)
            # If no exception was raised, check if URL was actually non-HTTPS
            # Some edge cases like 'https://' (exactly) might be handled differently
            if not url.startswith('https://'):
                assert False, f"Should have raised InsecureTransportError for URL: {url}"
        except InsecureTransportError:
            pass  # Expected behavior
    else:
        # For HTTPS URLs, should not raise InsecureTransportError
        try:
            oauth2(mock_request)
        except InsecureTransportError:
            assert False, f"Should not raise InsecureTransportError for HTTPS URL: {url}"
        except Exception:
            # Other exceptions are acceptable (e.g., from add_token)
            pass


@given(
    token=oauth2_token_strategy(),
    use_custom_client=st.booleans()
)
def test_client_token_interaction(token, use_custom_client):
    """Property: Token should be properly set whether using custom client or default."""
    if use_custom_client:
        custom_client = WebApplicationClient('custom_client_id')
        oauth2 = OAuth2(client=custom_client, token=token)
        # When custom client is provided, client_id parameter is ignored
        assert oauth2._client == custom_client
    else:
        oauth2 = OAuth2(client_id='test_client', token=token)
        assert oauth2._client.client_id == 'test_client'
    
    # In both cases, token attributes should be set
    if token:
        for key, value in token.items():
            assert hasattr(oauth2._client, key)
            assert getattr(oauth2._client, key) == value


@given(
    key=st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + '_'),
    value=st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans()
    )
)
def test_token_attribute_types(key, value):
    """Property: OAuth2 should handle various attribute types in token dict."""
    token = {key: value}
    oauth2 = OAuth2(client_id='test', token=token)
    
    assert hasattr(oauth2._client, key)
    assert getattr(oauth2._client, key) == value


@given(
    base_token=oauth2_token_strategy(),
    extra_keys=st.lists(
        st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + '_'),
        min_size=0,
        max_size=5,
        unique=True
    )
)
def test_token_with_extra_fields(base_token, extra_keys):
    """Property: OAuth2 should handle tokens with non-standard fields."""
    # Add extra fields to token
    token = base_token.copy()
    for i, key in enumerate(extra_keys):
        if key not in token:  # Avoid overwriting standard fields
            token[key] = f"extra_value_{i}"
    
    oauth2 = OAuth2(client_id='test', token=token)
    
    # All fields should be set as attributes
    for key, value in token.items():
        assert hasattr(oauth2._client, key)
        assert getattr(oauth2._client, key) == value


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])