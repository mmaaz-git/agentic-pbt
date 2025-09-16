import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from requests_oauthlib.oauth2_auth import OAuth2
from oauthlib.oauth2 import WebApplicationClient, InsecureTransportError
from unittest.mock import Mock
import string


@given(token_dict=st.one_of(
    st.just(None),
    st.just([]),  # List instead of dict
    st.just("token_string"),  # String instead of dict
    st.just(123),  # Integer instead of dict
    st.just({"items": "this_conflicts"}),  # Dict with 'items' key which might conflict
))
def test_non_dict_token_types(token_dict):
    """Test OAuth2 with non-dictionary token types."""
    try:
        oauth2 = OAuth2(client_id='test', token=token_dict)
        # If it works with non-dict, verify behavior
        if token_dict and hasattr(token_dict, 'items'):
            # Should iterate over items
            for k, v in token_dict.items():
                assert hasattr(oauth2._client, k)
    except (AttributeError, TypeError) as e:
        # These are expected for non-dict types
        if token_dict is not None and not hasattr(token_dict, 'items'):
            pass  # Expected failure
        else:
            raise  # Unexpected failure


@given(st.data())
def test_url_validation_edge_cases(data):
    """Test edge cases in HTTPS URL validation."""
    oauth2 = OAuth2(client_id='test', token={'access_token': 'test', 'token_type': 'Bearer'})
    
    # Test various URL patterns
    test_urls = [
        'HTTPS://example.com',  # Uppercase
        'hTtPs://example.com',  # Mixed case
        'https://',  # Just protocol
        'https:',  # Incomplete
        'http://example.com',  # Plain HTTP
        'ftp://example.com',  # Different protocol
        '',  # Empty string
        'https://example.com\nhttp://evil.com',  # URL with newline
        'https://example.com#http://evil.com',  # URL with fragment
    ]
    
    url = data.draw(st.sampled_from(test_urls))
    
    mock_request = Mock()
    mock_request.url = url
    mock_request.method = 'GET'
    mock_request.body = None
    mock_request.headers = {}
    
    try:
        result = oauth2(mock_request)
        # If it succeeded, URL should be HTTPS
        assert url.lower().startswith('https://'), f"Non-HTTPS URL {url} was accepted"
    except InsecureTransportError:
        # Should only raise for non-HTTPS
        assert not url.lower().startswith('https://'), f"HTTPS URL {url} was rejected"
    except Exception as e:
        # Other exceptions might be from add_token
        pass


@given(
    special_keys=st.lists(
        st.sampled_from(['__init__', '__class__', '__dict__', '_client', 'items', '__setattr__']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_token_with_special_attribute_names(special_keys):
    """Test token dict with keys that might conflict with object attributes."""
    token = {'access_token': 'test', 'token_type': 'Bearer'}
    for key in special_keys:
        token[key] = f'special_{key}'
    
    oauth2 = OAuth2(client_id='test', token=token)
    
    # Check if special attributes were set (this might overwrite important attributes!)
    for key in special_keys:
        if hasattr(oauth2._client, key):
            client_attr = getattr(oauth2._client, key)
            # Check if it was overwritten
            if callable(client_attr):
                # Method wasn't overwritten (good)
                pass
            else:
                # Attribute was set/overwritten
                assert client_attr == f'special_{key}', f"Special attribute {key} handling issue"


@given(st.data())
def test_request_modification_idempotence(data):
    """Test if calling OAuth2 auth multiple times on same request causes issues."""
    oauth2 = OAuth2(client_id='test', token={'access_token': 'mytoken', 'token_type': 'Bearer'})
    
    mock_request = Mock()
    mock_request.url = 'https://api.example.com/endpoint'
    mock_request.method = 'GET'
    mock_request.body = None
    mock_request.headers = {}
    
    # Apply auth once
    oauth2(mock_request)
    original_url = mock_request.url
    original_headers = mock_request.headers.copy()
    
    # Apply auth again - what happens?
    oauth2(mock_request)
    
    # Check if token was added twice or URL was modified twice
    # This might reveal if the auth is idempotent


@given(
    client_id=st.text(min_size=0, max_size=1000, alphabet=string.printable),
    has_null_bytes=st.booleans()
)  
def test_client_id_edge_cases(client_id, has_null_bytes):
    """Test OAuth2 with unusual client_id values."""
    if has_null_bytes:
        client_id = client_id[:50] + '\x00' + client_id[50:]
    
    oauth2 = OAuth2(client_id=client_id)
    assert oauth2._client.client_id == client_id


@given(st.data())
def test_empty_token_dict(data):
    """Test OAuth2 with empty token dictionary."""
    oauth2 = OAuth2(client_id='test', token={})
    
    # Empty dict should not cause issues
    assert oauth2._client is not None
    
    # Try to use it
    mock_request = Mock()
    mock_request.url = 'https://api.example.com'
    mock_request.method = 'GET'
    mock_request.body = None
    mock_request.headers = {}
    
    try:
        oauth2(mock_request)
        # Should work even with empty token
    except Exception as e:
        # Check what kind of exception
        pass


@given(
    value=st.one_of(
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan')),
        st.just(complex(1, 2)),
        st.just(lambda x: x),  # Function
        st.just(object()),  # Generic object
        st.just(type),  # Type object
    )
)
def test_token_with_unusual_value_types(value):
    """Test token dict with unusual value types."""
    token = {'access_token': 'test', 'token_type': 'Bearer', 'special_value': value}
    
    try:
        oauth2 = OAuth2(client_id='test', token=token)
        # Check if the unusual value was set
        assert hasattr(oauth2._client, 'special_value')
        client_value = getattr(oauth2._client, 'special_value')
        # NaN needs special comparison
        if isinstance(value, float) and value != value:  # NaN check
            assert client_value != client_value  # Should also be NaN
        else:
            assert client_value == value or client_value is value
    except Exception as e:
        # Some values might not be settable as attributes
        pass


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])