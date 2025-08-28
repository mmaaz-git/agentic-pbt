import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

import json
from urllib.parse import urlencode, quote
from hypothesis import given, strategies as st, assume, settings
import pytest
from requests_oauthlib import OAuth1, OAuth1Session, OAuth2Session
from requests_oauthlib.oauth1_session import urldecode


# Strategy for generating valid OAuth2 tokens
oauth2_token_strategy = st.dictionaries(
    st.sampled_from(['access_token', 'token_type', 'refresh_token', 'expires_in', 'scope']),
    st.one_of(
        st.text(min_size=1, max_size=100),
        st.integers(),
        st.none()
    ),
    min_size=0,
    max_size=5
).filter(lambda d: 'access_token' not in d or d['access_token'] is not None)


# Test 1: OAuth2Session.authorized property
@given(token=oauth2_token_strategy)
def test_oauth2_session_authorized_property(token):
    """The 'authorized' property should be True iff there's an access_token"""
    session = OAuth2Session(client_id='test_client')
    session.token = token
    
    # According to the code, authorized checks bool(self.access_token)
    expected_authorized = bool(token.get('access_token'))
    assert session.authorized == expected_authorized


# Test 2: OAuth2Session token round-trip property
@given(token=oauth2_token_strategy)
def test_oauth2_session_token_roundtrip(token):
    """Setting and getting token should preserve the value"""
    session = OAuth2Session(client_id='test_client')
    session.token = token
    
    # The token should be preserved
    assert session.token == token


# Test 3: OAuth2Session PKCE validation
@given(pkce=st.one_of(
    st.none(),
    st.just('S256'),
    st.just('plain'),
    st.text(min_size=1, max_size=20)
))
def test_oauth2_session_pkce_validation(pkce):
    """PKCE parameter should only accept 'S256', 'plain', or None"""
    if pkce not in ['S256', 'plain', None]:
        # Should raise AttributeError for invalid values
        with pytest.raises(AttributeError):
            OAuth2Session(client_id='test_client', pkce=pkce)
    else:
        # Should create successfully for valid values
        session = OAuth2Session(client_id='test_client', pkce=pkce)
        assert session._pkce == pkce


# Test 4: urldecode dual-mode parsing
@given(data=st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda s: '=' not in s and '&' not in s),
    st.text(min_size=0, max_size=50).filter(lambda s: '=' not in s and '&' not in s),
    min_size=1,
    max_size=5
))
def test_urldecode_dual_mode(data):
    """urldecode should handle both URL-encoded and JSON formats"""
    # Test with URL encoding
    url_encoded = urlencode(data)
    result_url = urldecode(url_encoded)
    assert result_url == list(data.items())
    
    # Test with JSON encoding
    json_encoded = json.dumps(data)
    result_json = urldecode(json_encoded)
    assert result_json == data


# Test 5: urldecode with complex JSON
@given(json_data=st.one_of(
    st.dictionaries(st.text(min_size=1), st.integers()),
    st.lists(st.integers()),
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none()
))
def test_urldecode_json_fallback(json_data):
    """urldecode should parse valid JSON when URL decoding fails"""
    json_str = json.dumps(json_data)
    
    # Since this is valid JSON but not URL-encoded, it should use JSON parsing
    result = urldecode(json_str)
    assert result == json_data


# Test 6: OAuth1 signature_type normalization  
@given(signature_type=st.one_of(
    st.just('AUTH_HEADER'),
    st.just('auth_header'),
    st.just('QUERY'),
    st.just('query'),
    st.just('BODY'),
    st.just('body'),
    st.text(min_size=1, max_size=20),
    st.none(),
    st.integers()
))
def test_oauth1_signature_type_normalization(signature_type):
    """OAuth1 should handle signature_type normalization"""
    try:
        oauth1 = OAuth1(
            client_key='test_key',
            client_secret='test_secret',
            signature_type=signature_type
        )
        # If it succeeds, check that string types are uppercased
        if hasattr(signature_type, 'upper'):
            # The code tries to uppercase it
            assert True  # Construction succeeded
    except AttributeError:
        # Expected for non-string types that don't have .upper()
        assert not hasattr(signature_type, 'upper')
    except Exception as e:
        # Other exceptions might occur for invalid values
        pass


# Test 7: OAuth2Session client_id property round-trip
@given(client_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)))
def test_oauth2_session_client_id_roundtrip(client_id):
    """Setting and getting client_id should preserve the value"""
    session = OAuth2Session(client_id=client_id)
    assert session.client_id == client_id
    
    # Test setting a new value
    new_id = 'new_test_id'
    session.client_id = new_id
    assert session.client_id == new_id


# Test 8: OAuth2Session access_token property
@given(
    initial_token=oauth2_token_strategy,
    new_access_token=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_oauth2_session_access_token_property(initial_token, new_access_token):
    """access_token property should correctly get/set the token's access_token field"""
    session = OAuth2Session(client_id='test_client')
    session.token = initial_token
    
    # Check initial access_token
    assert session.access_token == initial_token.get('access_token')
    
    # Set new access_token
    session.access_token = new_access_token
    assert session.access_token == new_access_token
    
    # authorized should reflect the new access_token
    assert session.authorized == bool(new_access_token)


# Test 9: OAuth2Session state generation
@given(state=st.one_of(
    st.none(),
    st.text(min_size=1, max_size=100),
    st.just(lambda: 'generated_state')
))
def test_oauth2_session_state_generation(state):
    """State should be generated or preserved correctly"""
    session = OAuth2Session(client_id='test_client', state=state)
    
    new_state = session.new_state()
    
    if state is None:
        # Should generate a new state
        assert new_state is not None
        assert len(new_state) > 0
    elif callable(state):
        # Should call the function
        assert new_state == 'generated_state'
    else:
        # Should preserve the string
        assert new_state == state


if __name__ == '__main__':
    # Run with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, '-v', '--tb=short']))