import sys
import os
import json
import re
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

from trino.auth import (
    BasicAuthentication,
    JWTAuthentication,
    CertificateAuthentication,
    KerberosAuthentication,
    GSSAPIAuthentication,
    _OAuth2TokenBearer,
    _OAuth2KeyRingTokenCache,
    _OAuth2TokenInMemoryCache,
)
from trino.constants import MAX_NT_PASSWORD_SIZE


# Strategy for creating authentication objects
@st.composite
def basic_auth_strategy(draw):
    username = draw(st.text(min_size=1, max_size=100))
    password = draw(st.text(min_size=1, max_size=100))
    return BasicAuthentication(username, password)


@st.composite
def jwt_auth_strategy(draw):
    token = draw(st.text(min_size=1, max_size=1000))
    return JWTAuthentication(token)


@st.composite
def cert_auth_strategy(draw):
    cert = draw(st.text(min_size=1, max_size=200))
    key = draw(st.text(min_size=1, max_size=200))
    return CertificateAuthentication(cert, key)


@st.composite
def kerberos_auth_strategy(draw):
    config = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    service_name = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    mutual_auth = draw(st.sampled_from([1, 2, 3]))
    force_preemptive = draw(st.booleans())
    hostname_override = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    sanitize = draw(st.booleans())
    principal = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    delegate = draw(st.booleans())
    ca_bundle = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    return KerberosAuthentication(
        config, service_name, mutual_auth, force_preemptive,
        hostname_override, sanitize, principal, delegate, ca_bundle
    )


@st.composite
def gssapi_auth_strategy(draw):
    config = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    service_name = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    mutual_auth = draw(st.sampled_from([1, 2, 3]))
    force_preemptive = draw(st.booleans())
    hostname_override = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    sanitize = draw(st.booleans())
    principal = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    delegate = draw(st.booleans())
    ca_bundle = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    return GSSAPIAuthentication(
        config, service_name, mutual_auth, force_preemptive,
        hostname_override, sanitize, principal, delegate, ca_bundle
    )


# Test 1: Authentication equality is reflexive
@given(basic_auth_strategy())
def test_basic_auth_equality_reflexive(auth):
    assert auth == auth


@given(jwt_auth_strategy())
def test_jwt_auth_equality_reflexive(auth):
    assert auth == auth


@given(cert_auth_strategy())
def test_cert_auth_equality_reflexive(auth):
    assert auth == auth


@given(kerberos_auth_strategy())
def test_kerberos_auth_equality_reflexive(auth):
    assert auth == auth


@given(gssapi_auth_strategy())
def test_gssapi_auth_equality_reflexive(auth):
    assert auth == auth


# Test 2: Authentication equality is symmetric
@given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=100))
def test_basic_auth_equality_symmetric(username, password):
    auth1 = BasicAuthentication(username, password)
    auth2 = BasicAuthentication(username, password)
    assert auth1 == auth2
    assert auth2 == auth1


@given(st.text(min_size=1, max_size=1000))
def test_jwt_auth_equality_symmetric(token):
    auth1 = JWTAuthentication(token)
    auth2 = JWTAuthentication(token)
    assert auth1 == auth2
    assert auth2 == auth1


# Test 3: Authentication inequality with different values
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_basic_auth_inequality(user1, pass1, user2, pass2):
    assume(user1 != user2 or pass1 != pass2)
    auth1 = BasicAuthentication(user1, pass1)
    auth2 = BasicAuthentication(user2, pass2)
    assert auth1 != auth2


# Test 4: OAuth2 password sharding round-trip
@given(st.text(min_size=MAX_NT_PASSWORD_SIZE + 1, max_size=MAX_NT_PASSWORD_SIZE * 3))
@settings(max_examples=20)
def test_oauth2_password_sharding_roundtrip(token):
    # Mock keyring
    storage = {}
    
    def mock_set_password(service, username, password):
        storage[f"{service}:{username}"] = password
    
    def mock_get_password(service, username):
        return storage.get(f"{service}:{username}")
    
    with patch('importlib.import_module') as mock_import:
        mock_keyring = MagicMock()
        mock_keyring.get_password = mock_get_password
        mock_keyring.set_password = mock_set_password
        mock_keyring.get_keyring.return_value = MagicMock()
        mock_keyring.backends.fail.Keyring = type('Keyring', (), {})
        mock_import.return_value = mock_keyring
        
        cache = _OAuth2KeyRingTokenCache()
        cache._keyring = mock_keyring
        
        # Simulate Windows environment for sharding
        original_os_name = os.name
        try:
            os.name = 'nt'
            key = "test_host@test_user"
            
            # Store token (should be sharded)
            cache.store_token_to_cache(key, token)
            
            # Retrieve token (should reconstruct from shards)
            retrieved_token = cache.get_token_from_cache(key)
            
            assert retrieved_token == token
        finally:
            os.name = original_os_name


# Test 5: Authentication header parsing
@given(st.dictionaries(
    st.from_regex(r'[a-zA-Z][a-zA-Z0-9_-]*', fullmatch=True),
    st.text(min_size=1, max_size=100),
    min_size=1,
    max_size=10
))
def test_authentication_header_parsing(headers_dict):
    # Create header string from dictionary
    header_parts = []
    for key, value in headers_dict.items():
        # Quote values with spaces or special characters
        if ' ' in value or ',' in value:
            header_parts.append(f'{key}="{value}"')
        else:
            header_parts.append(f'{key}={value}')
    
    header = ', '.join(header_parts)
    
    # Parse the header
    parsed = _OAuth2TokenBearer._parse_authenticate_header(header)
    
    # Check that all keys are lowercase in the result
    for key in parsed.keys():
        assert key == key.lower()
    
    # Check that values are correctly parsed (without quotes)
    for original_key, original_value in headers_dict.items():
        parsed_value = parsed.get(original_key.lower())
        assert parsed_value == original_value


# Test 6: Cache key construction consistency
@given(
    st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_cache_key_construction(host, user):
    key1 = _OAuth2TokenBearer._construct_cache_key(host, user)
    key2 = _OAuth2TokenBearer._construct_cache_key(host, user)
    
    # Same inputs should produce same keys
    assert key1 == key2
    
    # Check the format
    if user is None:
        assert key1 == host
    else:
        assert key1 == f"{host}@{user}"


# Test 7: Bearer prefix case-insensitive matching
@given(st.sampled_from(['bearer', 'Bearer', 'BEARER', 'BeArEr', 'bEaReR']))
def test_bearer_prefix_case_insensitive(bearer_text):
    pattern = _OAuth2TokenBearer._BEARER_PREFIX
    test_string = f"{bearer_text} token=abc123"
    
    match = pattern.search(test_string)
    assert match is not None


# Test 8: In-memory token cache round-trip
@given(
    st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    st.text(min_size=1, max_size=1000)
)
def test_inmemory_cache_roundtrip(key, token):
    cache = _OAuth2TokenInMemoryCache()
    
    # Initially, cache should be empty
    assert cache.get_token_from_cache(key) is None
    
    # Store token
    cache.store_token_to_cache(key, token)
    
    # Retrieve token
    retrieved = cache.get_token_from_cache(key)
    assert retrieved == token
    
    # Store different token with same key should overwrite
    new_token = token + "_modified"
    cache.store_token_to_cache(key, new_token)
    retrieved = cache.get_token_from_cache(key)
    assert retrieved == new_token


# Test 9: Authentication header with edge cases
@given(st.text(min_size=1, max_size=200))
def test_authentication_header_parsing_with_equals_in_value(value):
    # Values can contain '=' signs
    assume('=' in value)
    header = f'key="{value}"'
    parsed = _OAuth2TokenBearer._parse_authenticate_header(header)
    assert parsed['key'] == value


# Test 10: Multiple authentication types don't equal each other
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_different_auth_types_not_equal(text1, text2):
    basic = BasicAuthentication(text1, text2)
    jwt = JWTAuthentication(text1)
    cert = CertificateAuthentication(text1, text2)
    
    assert basic != jwt
    assert basic != cert
    assert jwt != cert
    assert basic != "not_an_auth_object"
    assert jwt != None