#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import json
import re
from hypothesis import given, strategies as st, assume
from hypothesis import settings
import trino.auth as auth


# Strategy for generating reasonable authentication parameters
safe_string = st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and not any(c in x for c in ['\x00', '\n', '\r']))
url_string = st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=100)
optional_string = st.one_of(st.none(), safe_string)
boolean_strategy = st.booleans()
mutual_auth_strategy = st.sampled_from([1, 2, 3])  # REQUIRED, OPTIONAL, DISABLED


# Test 1: Equality properties for authentication classes
@given(
    username=safe_string,
    password=safe_string
)
def test_basic_auth_equality_reflexive(username, password):
    """Test that BasicAuthentication equality is reflexive"""
    auth1 = auth.BasicAuthentication(username, password)
    assert auth1 == auth1


@given(
    username=safe_string,
    password=safe_string
)
def test_basic_auth_equality_consistent(username, password):
    """Test that BasicAuthentication with same params produces equal objects"""
    auth1 = auth.BasicAuthentication(username, password)
    auth2 = auth.BasicAuthentication(username, password)
    assert auth1 == auth2


@given(
    username1=safe_string,
    password1=safe_string,
    username2=safe_string,
    password2=safe_string
)
def test_basic_auth_inequality(username1, password1, username2, password2):
    """Test that BasicAuthentication with different params are not equal"""
    assume(username1 != username2 or password1 != password2)
    auth1 = auth.BasicAuthentication(username1, password1)
    auth2 = auth.BasicAuthentication(username2, password2)
    assert auth1 != auth2


@given(token=safe_string)
def test_jwt_auth_equality_reflexive(token):
    """Test that JWTAuthentication equality is reflexive"""
    jwt_auth = auth.JWTAuthentication(token)
    assert jwt_auth == jwt_auth


@given(token=safe_string)
def test_jwt_auth_equality_consistent(token):
    """Test that JWTAuthentication with same token produces equal objects"""
    jwt_auth1 = auth.JWTAuthentication(token)
    jwt_auth2 = auth.JWTAuthentication(token)
    assert jwt_auth1 == jwt_auth2


@given(
    cert=safe_string,
    key=safe_string
)
def test_certificate_auth_equality_consistent(cert, key):
    """Test that CertificateAuthentication with same params produces equal objects"""
    auth1 = auth.CertificateAuthentication(cert, key)
    auth2 = auth.CertificateAuthentication(cert, key)
    assert auth1 == auth2


# Test 2: _parse_authenticate_header parsing logic
@given(
    components=st.lists(
        st.tuples(
            st.text(alphabet=st.characters(blacklist_characters='=,"\n\r'), min_size=1, max_size=20),
            st.text(min_size=0, max_size=50).filter(lambda x: '\n' not in x and '\r' not in x)
        ),
        min_size=1,
        max_size=10
    )
)
def test_parse_authenticate_header_lowercases_keys(components):
    """Test that _parse_authenticate_header lowercases all keys"""
    # Construct header from components
    header_parts = []
    for key, value in components:
        # Add quotes around value if it contains special chars
        if ',' in value or ' ' in value:
            header_parts.append(f'{key}="{value}"')
        else:
            header_parts.append(f'{key}={value}')
    
    header = ', '.join(header_parts)
    
    result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
    
    # All keys should be lowercase
    for key in result.keys():
        assert key == key.lower()


@given(
    key=st.text(alphabet=st.characters(blacklist_characters='=,"\n\r'), min_size=1, max_size=20),
    value=st.text(min_size=1, max_size=50).filter(lambda x: '\n' not in x and '\r' not in x and '"' not in x)
)
def test_parse_authenticate_header_strips_quotes(key, value):
    """Test that _parse_authenticate_header strips quotes from values"""
    # Test with quotes
    header_with_quotes = f'{key}="{value}"'
    result_with_quotes = auth._OAuth2TokenBearer._parse_authenticate_header(header_with_quotes)
    
    # Test without quotes  
    header_without_quotes = f'{key}={value}'
    result_without_quotes = auth._OAuth2TokenBearer._parse_authenticate_header(header_without_quotes)
    
    # Both should produce the same value (quotes stripped)
    assert result_with_quotes.get(key.lower()) == value
    assert result_without_quotes.get(key.lower()) == value


# Test 3: _construct_cache_key consistency
@given(
    host=st.one_of(st.none(), safe_string),
    user=st.one_of(st.none(), safe_string)
)
def test_construct_cache_key_format(host, user):
    """Test that _construct_cache_key produces expected format"""
    result = auth._OAuth2TokenBearer._construct_cache_key(host, user)
    
    if user is None:
        assert result == host
    else:
        assert result == f"{host}@{user}"


@given(
    host=st.one_of(st.none(), safe_string),
    user=st.one_of(st.none(), safe_string)
)
def test_construct_cache_key_deterministic(host, user):
    """Test that _construct_cache_key is deterministic"""
    result1 = auth._OAuth2TokenBearer._construct_cache_key(host, user)
    result2 = auth._OAuth2TokenBearer._construct_cache_key(host, user)
    assert result1 == result2


# Test 4: OAuth2 token cache round-trip operations
@given(
    key=st.one_of(st.none(), safe_string),
    token=safe_string
)
def test_in_memory_cache_round_trip(key, token):
    """Test that storing and retrieving from in-memory cache is consistent"""
    cache = auth._OAuth2TokenInMemoryCache()
    
    # Initially should be None
    assert cache.get_token_from_cache(key) is None
    
    # Store token
    cache.store_token_to_cache(key, token)
    
    # Retrieve should match what was stored
    retrieved = cache.get_token_from_cache(key)
    assert retrieved == token


@given(
    key=st.one_of(st.none(), safe_string),
    token1=safe_string,
    token2=safe_string
)
def test_in_memory_cache_overwrite(key, token1, token2):
    """Test that storing a new token overwrites the old one"""
    cache = auth._OAuth2TokenInMemoryCache()
    
    # Store first token
    cache.store_token_to_cache(key, token1)
    assert cache.get_token_from_cache(key) == token1
    
    # Store second token with same key
    cache.store_token_to_cache(key, token2)
    assert cache.get_token_from_cache(key) == token2


@given(
    keys_and_tokens=st.lists(
        st.tuples(
            st.one_of(st.none(), safe_string),
            safe_string
        ),
        min_size=1,
        max_size=10
    )
)
def test_in_memory_cache_multiple_keys(keys_and_tokens):
    """Test that cache correctly handles multiple keys"""
    cache = auth._OAuth2TokenInMemoryCache()
    
    # Store all tokens
    for key, token in keys_and_tokens:
        cache.store_token_to_cache(key, token)
    
    # Retrieve and verify all tokens
    # Latest value for each key should be retrievable
    key_to_token = {}
    for key, token in keys_and_tokens:
        key_to_token[key] = token  # This will keep the latest value for each key
    
    for key, expected_token in key_to_token.items():
        assert cache.get_token_from_cache(key) == expected_token


# Test 5: URL host extraction
@given(
    scheme=st.sampled_from(['http', 'https']),
    host=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    path=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=0, max_size=20)
)
def test_determine_host_extracts_hostname(scheme, host, port, path):
    """Test that _determine_host correctly extracts hostname from URL"""
    if port is not None:
        url = f"{scheme}://{host}:{port}/{path}"
    else:
        url = f"{scheme}://{host}/{path}"
    
    result = auth._OAuth2TokenBearer._determine_host(url)
    assert result == host


# Test 6: Equality properties are symmetric
@given(
    username=safe_string,
    password=safe_string
)
def test_basic_auth_equality_symmetric(username, password):
    """Test that BasicAuthentication equality is symmetric"""
    auth1 = auth.BasicAuthentication(username, password)
    auth2 = auth.BasicAuthentication(username, password)
    assert (auth1 == auth2) == (auth2 == auth1)


# Test 7: Different authentication types are never equal
@given(
    token=safe_string,
    username=safe_string,
    password=safe_string,
    cert=safe_string,
    key=safe_string
)
def test_different_auth_types_not_equal(token, username, password, cert, key):
    """Test that different authentication types are never equal"""
    jwt_auth = auth.JWTAuthentication(token)
    basic_auth = auth.BasicAuthentication(username, password)
    cert_auth = auth.CertificateAuthentication(cert, key)
    
    assert jwt_auth != basic_auth
    assert jwt_auth != cert_auth
    assert basic_auth != cert_auth
    
    # Also test against non-authentication objects
    assert jwt_auth != token
    assert basic_auth != username
    assert cert_auth != cert


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])