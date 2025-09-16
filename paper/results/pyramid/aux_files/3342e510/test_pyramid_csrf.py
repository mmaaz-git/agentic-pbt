#!/usr/bin/env python3
"""Property-based tests for pyramid.csrf module using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import random
import string
import uuid
from unittest.mock import MagicMock, Mock, patch
from hypothesis import assume, given, strategies as st, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize
import pytest

from pyramid.util import SimpleSerializer, is_same_domain, strings_differ, text_, bytes_
from pyramid.csrf import (
    SessionCSRFStoragePolicy,
    CookieCSRFStoragePolicy,
    check_csrf_origin,
)


# Test 1: SimpleSerializer round-trip property
@given(st.text())
def test_simple_serializer_round_trip(text):
    """SimpleSerializer should correctly round-trip text strings."""
    serializer = SimpleSerializer()
    
    # Convert text to bytes and back
    serialized = serializer.dumps(text)
    deserialized = serializer.loads(serialized)
    
    assert deserialized == text, f"Round-trip failed: {text!r} != {deserialized!r}"


# Test 2: strings_differ correctness - should detect differences correctly
@given(st.text(min_size=1), st.text(min_size=1))
def test_strings_differ_correctness(s1, s2):
    """strings_differ should correctly identify whether strings are different."""
    # Convert to bytes for comparison
    b1 = bytes_(s1)
    b2 = bytes_(s2)
    
    result = strings_differ(b1, b2)
    expected = (b1 != b2)
    
    assert result == expected, f"strings_differ({b1!r}, {b2!r}) returned {result}, expected {expected}"


# Test 3: strings_differ with same strings
@given(st.text(min_size=1))
def test_strings_differ_same_string(s):
    """strings_differ should return False for identical strings."""
    b = bytes_(s)
    result = strings_differ(b, b)
    assert result == False, f"strings_differ should return False for identical strings"


# Test 4: is_same_domain wildcard matching
@given(
    st.text(min_size=1, alphabet=string.ascii_lowercase + string.digits + '-.'),
    st.text(min_size=1, alphabet=string.ascii_lowercase + string.digits + '-.')
)
def test_is_same_domain_exact_match(host, pattern):
    """is_same_domain should match exact domain names (case-insensitive)."""
    # Test exact match (case insensitive)
    assert is_same_domain(host.lower(), host.lower()) == True
    assert is_same_domain(host.lower(), host.upper()) == True
    assert is_same_domain(host.upper(), host.lower()) == True
    
    # Different domains should not match (unless pattern is wildcard)
    if not pattern.startswith('.') and host.lower() != pattern.lower():
        assert is_same_domain(host, pattern) == False


@given(
    st.text(min_size=1, max_size=20, alphabet=string.ascii_lowercase),
    st.text(min_size=1, max_size=20, alphabet=string.ascii_lowercase)
)
def test_is_same_domain_wildcard(subdomain, domain):
    """Test wildcard domain matching with leading dot."""
    assume(subdomain and domain)  # Non-empty strings
    assume('.' not in subdomain and '.' not in domain)  # Simple labels
    
    # Wildcard pattern
    pattern = f".{domain}"
    
    # Should match the domain itself
    assert is_same_domain(domain, pattern) == True
    
    # Should match subdomains
    full_domain = f"{subdomain}.{domain}"
    assert is_same_domain(full_domain, pattern) == True
    
    # Should match deeper subdomains
    deep_domain = f"deep.{subdomain}.{domain}"
    assert is_same_domain(deep_domain, pattern) == True


@given(st.text(min_size=1, max_size=50, alphabet=string.ascii_lowercase + '.'))
def test_is_same_domain_empty_pattern(host):
    """is_same_domain should return False for empty pattern."""
    assert is_same_domain(host, "") == False
    assert is_same_domain(host, None) == False


# Test 5: SessionCSRFStoragePolicy token generation and retrieval
@given(st.text(min_size=5, max_size=20))
def test_session_csrf_policy_token_consistency(session_key):
    """Token set via new_csrf_token should be retrievable via get_csrf_token."""
    policy = SessionCSRFStoragePolicy(key=session_key)
    
    # Mock request with session
    request = Mock()
    request.session = {}
    
    # Generate new token
    token1 = policy.new_csrf_token(request)
    
    # Token should be stored in session
    assert session_key in request.session
    assert request.session[session_key] == token1
    
    # get_csrf_token should return the same token
    token2 = policy.get_csrf_token(request)
    assert token2 == token1
    
    # Multiple calls to get_csrf_token should return same token
    token3 = policy.get_csrf_token(request)
    assert token3 == token1


# Test 6: Token uniqueness
def test_token_generation_uniqueness():
    """Multiple token generations should produce unique values."""
    policy = SessionCSRFStoragePolicy()
    tokens = set()
    
    for _ in range(100):
        token = policy._token_factory()
        assert token not in tokens, f"Duplicate token generated: {token}"
        tokens.add(token)
        # Tokens should be hex strings from UUID
        assert len(token) == 32  # UUID4 hex is 32 chars
        assert all(c in string.hexdigits for c in token)


# Test 7: check_csrf_token validation
@given(st.text(min_size=10, max_size=50, alphabet=string.ascii_letters + string.digits))
def test_session_csrf_token_validation(token):
    """A token should be validated correctly by check_csrf_token."""
    policy = SessionCSRFStoragePolicy()
    
    # Mock request
    request = Mock()
    request.session = {}
    
    # Set a specific token
    request.session[policy.key] = token
    
    # Should validate the same token
    assert policy.check_csrf_token(request, token) == True
    
    # Should reject different token
    different_token = token + "X"
    assert policy.check_csrf_token(request, different_token) == False


# Test 8: CookieCSRFStoragePolicy 
@given(
    st.text(min_size=5, max_size=20, alphabet=string.ascii_lowercase),
    st.booleans(),
    st.booleans()
)
def test_cookie_csrf_policy_initialization(cookie_name, secure, httponly):
    """CookieCSRFStoragePolicy should initialize with correct parameters."""
    policy = CookieCSRFStoragePolicy(
        cookie_name=cookie_name,
        secure=secure,
        httponly=httponly
    )
    
    assert policy.cookie_name == cookie_name
    assert policy.cookie_profile.cookie_name == cookie_name
    assert policy.cookie_profile.secure == secure
    assert policy.cookie_profile.httponly == httponly


# Test 9: check_csrf_origin with HTTPS
@given(
    st.text(min_size=3, max_size=20, alphabet=string.ascii_lowercase),
    st.integers(min_value=1, max_value=65535)
)
def test_check_csrf_origin_same_origin(domain, port):
    """check_csrf_origin should accept requests from same origin."""
    request = Mock()
    request.scheme = "https"
    request.domain = domain
    request.host_port = str(port)
    request.headers = {"Origin": f"https://{domain}:{port}"}
    request.referrer = None
    request.registry = Mock()
    request.registry.settings = {}
    
    # Same origin should pass
    result = check_csrf_origin(request, raises=False)
    assert result == True


# Test 10: Edge cases for is_same_domain
def test_is_same_domain_edge_cases():
    """Test edge cases for is_same_domain function."""
    # Wildcard should match domain and subdomains
    assert is_same_domain("example.com", ".example.com") == True
    assert is_same_domain("sub.example.com", ".example.com") == True
    assert is_same_domain("deep.sub.example.com", ".example.com") == True
    
    # But not unrelated domains
    assert is_same_domain("notexample.com", ".example.com") == False
    assert is_same_domain("example.org", ".example.com") == False
    
    # Edge case: pattern is just "."
    assert is_same_domain("any.domain", ".") == True
    assert is_same_domain("", ".") == False
    
    # Case insensitive
    assert is_same_domain("EXAMPLE.COM", "example.com") == True
    assert is_same_domain("example.com", "EXAMPLE.COM") == True


# Test 11: Multiple token generation should be unique
def test_multiple_storage_policies_unique_tokens():
    """Different storage policy instances should generate unique tokens."""
    policies = [SessionCSRFStoragePolicy() for _ in range(10)]
    tokens = []
    
    for policy in policies:
        request = Mock()
        request.session = {}
        token = policy.new_csrf_token(request)
        tokens.append(token)
    
    # All tokens should be unique
    assert len(set(tokens)) == len(tokens), "Duplicate tokens generated across policies"


# Test 12: Token factory generates valid UUID hex strings
def test_token_factory_format():
    """Token factory should generate valid UUID hex strings."""
    policy = SessionCSRFStoragePolicy()
    
    for _ in range(100):
        token = policy._token_factory()
        # Should be a valid hex string
        assert all(c in string.hexdigits for c in token)
        # Should be 32 characters (UUID without hyphens)
        assert len(token) == 32
        # Should be parseable as UUID
        try:
            # Add hyphens back to parse as UUID
            uuid_str = f"{token[:8]}-{token[8:12]}-{token[12:16]}-{token[16:20]}-{token[20:]}"
            uuid.UUID(uuid_str)
        except ValueError:
            pytest.fail(f"Token {token} is not a valid UUID hex")


if __name__ == "__main__":
    # Run with pytest
    print("Running property-based tests for pyramid.csrf...")
    print("Use pytest to run these tests: pytest test_pyramid_csrf.py -v")