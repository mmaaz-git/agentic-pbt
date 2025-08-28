"""Property-based tests for pyramid.authentication module"""

import sys
import os
import base64
import time
import re
from hypothesis import given, strategies as st, assume, settings

# Add pyramid module to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.authentication import (
    b64encode, b64decode,
    AuthTicket, parse_ticket, BadTicket,
    calculate_digest, encode_ip_timestamp,
    extract_http_basic_credentials, HTTPBasicCredentials,
    VALID_TOKEN
)


# Test 1: Base64 round-trip property
@given(st.binary())
def test_b64_round_trip(data):
    """Test that b64decode(b64encode(data)) == data"""
    encoded = b64encode(data)
    decoded = b64decode(encoded)
    assert decoded == data


# Test 2: AuthTicket round-trip property  
@given(
    secret=st.text(min_size=1),
    userid=st.text(min_size=1),
    ip=st.from_regex(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'),  # IPv4 addresses
    tokens=st.lists(st.from_regex(r'^[A-Za-z][A-Za-z0-9+_-]*$'), max_size=5),
    user_data=st.text(),
    timestamp=st.floats(min_value=0, max_value=2**31-1, allow_nan=False),
    hashalg=st.sampled_from(['md5', 'sha1', 'sha256', 'sha512'])
)
def test_auth_ticket_round_trip(secret, userid, ip, tokens, user_data, timestamp, hashalg):
    """Test that creating and parsing auth tickets preserves data"""
    # Create ticket
    ticket = AuthTicket(
        secret=secret,
        userid=userid,
        ip=ip,
        tokens=tokens,
        user_data=user_data,
        time=timestamp,
        hashalg=hashalg
    )
    
    cookie_value = ticket.cookie_value()
    
    # Parse ticket
    try:
        parsed_timestamp, parsed_userid, parsed_tokens, parsed_user_data = parse_ticket(
            secret=secret,
            ticket=cookie_value,
            ip=ip,
            hashalg=hashalg
        )
        
        # Check round-trip
        assert int(timestamp) == parsed_timestamp
        assert userid == parsed_userid
        assert list(tokens) == parsed_tokens
        assert user_data == parsed_user_data
    except BadTicket:
        # This shouldn't happen with valid inputs
        assert False, f"Failed to parse valid ticket"


# Test 3: Token validation regex
@given(st.text())
def test_token_validation_regex(token):
    """Test that VALID_TOKEN regex correctly validates tokens"""
    matches = VALID_TOKEN.match(token) is not None
    
    # A token should match if and only if:
    # - It starts with a letter (A-Z or a-z)
    # - Followed by zero or more letters, digits, +, _, or -
    # - And nothing else (full match)
    
    if matches:
        # If it matches, verify it follows the pattern
        assert len(token) > 0
        assert token[0].isalpha()
        for char in token[1:]:
            assert char.isalnum() or char in '+_-'
    else:
        # If it doesn't match, it should violate the pattern
        if len(token) == 0:
            pass  # Empty strings don't match
        elif not token[0].isalpha():
            pass  # Doesn't start with letter
        else:
            # Must contain invalid characters
            has_invalid = False
            for char in token[1:]:
                if not (char.isalnum() or char in '+_-'):
                    has_invalid = True
                    break
            assert has_invalid or token == ''


# Test 4: HTTP Basic credentials parsing
@given(
    username=st.text(min_size=1).filter(lambda x: ':' not in x),
    password=st.text()
)
def test_extract_basic_credentials_valid(username, password):
    """Test parsing valid HTTP Basic auth headers"""
    # Create valid Basic auth header
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
    
    class MockRequest:
        headers = {'Authorization': f'Basic {encoded}'}
    
    result = extract_http_basic_credentials(MockRequest())
    
    assert result is not None
    assert isinstance(result, HTTPBasicCredentials)
    assert result.username == username
    assert result.password == password


@given(st.text())
def test_extract_basic_credentials_invalid(auth_header):
    """Test that invalid auth headers return None"""
    class MockRequest:
        headers = {'Authorization': auth_header} if auth_header else {}
    
    result = extract_http_basic_credentials(MockRequest())
    
    # Result should be None for most random strings
    # Only valid Basic auth headers should parse
    if result is not None:
        # If it parsed, verify it's actually valid
        assert auth_header.lower().startswith('basic ')
        try:
            auth_part = auth_header.split(' ', 1)[1]
            decoded = base64.b64decode(auth_part.strip())
            auth_str = decoded.decode('utf-8')  # or latin-1
            assert ':' in auth_str
        except:
            # If we can't decode it, the function shouldn't have returned a result
            assert False, f"Function returned result for invalid header: {auth_header}"


# Test 5: calculate_digest determinism
@given(
    ip=st.from_regex(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'),
    timestamp=st.integers(min_value=0, max_value=2**31-1),
    secret=st.text(min_size=1),
    userid=st.text(),
    tokens=st.text(),
    user_data=st.text(),
    hashalg=st.sampled_from(['md5', 'sha1', 'sha256', 'sha512'])
)
def test_calculate_digest_determinism(ip, timestamp, secret, userid, tokens, user_data, hashalg):
    """Test that calculate_digest is deterministic"""
    digest1 = calculate_digest(ip, timestamp, secret, userid, tokens, user_data, hashalg)
    digest2 = calculate_digest(ip, timestamp, secret, userid, tokens, user_data, hashalg)
    
    assert digest1 == digest2


# Test 6: encode_ip_timestamp for IPv4
@given(
    ip=st.from_regex(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'),
    timestamp=st.integers(min_value=0, max_value=2**32-1)
)
def test_encode_ip_timestamp(ip, timestamp):
    """Test encode_ip_timestamp produces consistent results"""
    # Filter out invalid IPs
    parts = ip.split('.')
    for part in parts:
        if int(part) > 255:
            assume(False)
    
    result = encode_ip_timestamp(ip, timestamp)
    
    # Should produce bytes
    assert isinstance(result, bytes)
    
    # Should be 8 bytes (4 for IP, 4 for timestamp)
    assert len(result) == 8
    
    # Test determinism
    result2 = encode_ip_timestamp(ip, timestamp)
    assert result == result2


# Test 7: Test IPv6 handling in calculate_digest
@given(
    ipv6=st.from_regex(r'^[0-9a-fA-F:]+$').filter(lambda x: ':' in x),
    timestamp=st.integers(min_value=0, max_value=2**31-1),
    secret=st.text(min_size=1),
    userid=st.text(),
    tokens=st.text(),
    user_data=st.text(),
    hashalg=st.sampled_from(['md5', 'sha1', 'sha256', 'sha512'])
)
def test_calculate_digest_ipv6(ipv6, timestamp, secret, userid, tokens, user_data, hashalg):
    """Test that calculate_digest handles IPv6 addresses differently"""
    # IPv6 addresses are handled with a different code path
    digest1 = calculate_digest(ipv6, timestamp, secret, userid, tokens, user_data, hashalg)
    digest2 = calculate_digest(ipv6, timestamp, secret, userid, tokens, user_data, hashalg)
    
    # Should still be deterministic
    assert digest1 == digest2
    
    # Should produce valid hex digest
    assert all(c in '0123456789abcdef' for c in digest1)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])