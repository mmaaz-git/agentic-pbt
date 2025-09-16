#!/usr/bin/env python3
"""Property-based tests for spnego.sspi module using Hypothesis."""

import sys
import os

# Add the pyspnego environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import functions to test
from spnego._context import split_username
from spnego._text import to_bytes, to_text
from spnego._credential import unify_credentials, Password, NTLMHash, CredentialCache


# Test 1: split_username function
# Property from docstring: "Will split a username in the Netlogon form `DOMAIN\\username`"
# Returns (domain, username) tuple

@given(st.text())
def test_split_username_with_backslash(username):
    """Test that usernames with backslashes are split correctly."""
    # Create a username with domain
    domain_user = f"DOMAIN\\{username}"
    domain, user = split_username(domain_user)
    
    # The function should split on the FIRST backslash
    assert domain == "DOMAIN"
    assert user == username
    

@given(st.text(min_size=1).filter(lambda x: "\\" not in x))
def test_split_username_without_backslash(username):
    """Test that usernames without backslashes return None for domain."""
    domain, user = split_username(username)
    
    # Per the code: if no backslash, domain should be None
    assert domain is None
    assert user == username


def test_split_username_none():
    """Test that None input returns (None, None) as documented."""
    domain, user = split_username(None)
    assert domain is None
    assert user is None


@given(st.text(min_size=1), st.text(min_size=1))
def test_split_username_multiple_backslashes(domain_str, user_str):
    """Test that only the first backslash is used for splitting."""
    # Ensure user_str contains backslashes
    user_with_backslash = f"{user_str}\\extra\\parts"
    full_username = f"{domain_str}\\{user_with_backslash}"
    
    domain, user = split_username(full_username)
    
    # Should split on FIRST backslash only (line 45: domain, username = username.split("\\", 1))
    assert domain == domain_str
    assert user == user_with_backslash


# Test 2: to_bytes and to_text round-trip properties
# These functions should be able to convert between bytes and text

@given(st.text())
def test_to_bytes_to_text_round_trip(text):
    """Test that converting text to bytes and back preserves the text."""
    # Convert text -> bytes -> text
    as_bytes = to_bytes(text)
    back_to_text = to_text(as_bytes)
    
    assert back_to_text == text
    assert isinstance(as_bytes, bytes)
    assert isinstance(back_to_text, str)


@given(st.binary())
def test_to_text_to_bytes_round_trip(data):
    """Test that converting bytes to text and back preserves the bytes (when valid UTF-8)."""
    try:
        # Only test with valid UTF-8 bytes
        data.decode('utf-8')
    except UnicodeDecodeError:
        assume(False)  # Skip invalid UTF-8
    
    as_text = to_text(data)
    back_to_bytes = to_bytes(as_text)
    
    assert back_to_bytes == data
    assert isinstance(as_text, str)
    assert isinstance(back_to_bytes, bytes)


@given(st.text())
def test_to_bytes_idempotent(text):
    """Test that to_bytes is idempotent - applying it twice gives same result."""
    once = to_bytes(text)
    twice = to_bytes(once)
    
    assert once == twice
    assert isinstance(once, bytes)
    assert isinstance(twice, bytes)


@given(st.binary())
def test_to_bytes_on_bytes_unchanged(data):
    """Test that to_bytes on bytes returns the same bytes."""
    result = to_bytes(data)
    assert result == data
    assert result is data  # Should be the same object


@given(st.text())
def test_to_text_on_text_unchanged(text):
    """Test that to_text on text returns the same text."""
    result = to_text(text)
    assert result == text
    assert result is text  # Should be the same object


# Test 3: Test nonstring parameter behaviors
def test_to_bytes_nonstring_passthru():
    """Test that nonstring='passthru' passes through non-string objects."""
    obj = object()
    result = to_bytes(obj, nonstring='passthru')
    assert result is obj


def test_to_text_nonstring_passthru():
    """Test that nonstring='passthru' passes through non-string objects."""
    obj = object()
    result = to_text(obj, nonstring='passthru')
    assert result is obj


def test_to_bytes_nonstring_empty():
    """Test that nonstring='empty' returns empty bytes for non-strings."""
    result = to_bytes(123, nonstring='empty')
    assert result == b""
    
    result = to_bytes(None, nonstring='empty')
    assert result == b""


def test_to_text_nonstring_empty():
    """Test that nonstring='empty' returns empty string for non-strings."""
    result = to_text(123, nonstring='empty')
    assert result == ""
    
    result = to_text(None, nonstring='empty')
    assert result == ""


# Test 4: unify_credentials function
# Tests the credential processing logic

def test_unify_credentials_none_returns_credcache():
    """Test that None username returns a CredentialCache."""
    creds = unify_credentials(None, None)
    assert len(creds) == 1
    assert isinstance(creds[0], CredentialCache)


@given(st.text(min_size=1))
def test_unify_credentials_username_only(username):
    """Test that username without password returns CredentialCache."""
    creds = unify_credentials(username, None)
    assert len(creds) == 1
    assert isinstance(creds[0], CredentialCache)
    assert creds[0].username == username


@given(st.text(min_size=1), st.text(min_size=1).filter(lambda x: ":" not in x or not all(c in '0123456789abcdefABCDEF:' for c in x)))
def test_unify_credentials_username_password(username, password):
    """Test that username with non-hash password returns Password credential."""
    # Filter ensures password is not an NTLM hash format
    creds = unify_credentials(username, password)
    assert len(creds) == 1
    assert isinstance(creds[0], Password)
    assert creds[0].username == username
    assert creds[0].password == password


def test_unify_credentials_list_passthrough():
    """Test that credential objects in a list are passed through."""
    cred1 = Password(username="user1", password="pass1")
    cred2 = CredentialCache(username="user2")
    
    creds = unify_credentials([cred1, cred2])
    assert len(creds) == 2
    assert creds[0] is cred1
    assert creds[1] is cred2


def test_unify_credentials_single_credential_becomes_list():
    """Test that a single credential object becomes a list."""
    cred = Password(username="user", password="pass")
    creds = unify_credentials(cred)
    assert len(creds) == 1
    assert creds[0] is cred


# Test encoding parameter edge cases
@given(st.text())
def test_to_bytes_with_different_errors_param(text):
    """Test to_bytes with different error handling."""
    # Should not raise with valid text
    strict = to_bytes(text, errors='strict')
    ignore = to_bytes(text, errors='ignore')
    replace = to_bytes(text, errors='replace')
    
    # All should produce bytes
    assert isinstance(strict, bytes)
    assert isinstance(ignore, bytes) 
    assert isinstance(replace, bytes)


if __name__ == "__main__":
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "--tb=short"])