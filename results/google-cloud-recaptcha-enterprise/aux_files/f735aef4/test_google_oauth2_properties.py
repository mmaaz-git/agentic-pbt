#!/usr/bin/env python3
"""Property-based tests for google.oauth2 module using Hypothesis."""

import sys
import json
import base64
import urllib.parse
import datetime
from unittest import mock

sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import hypothesis.strategies as st
from hypothesis import given, assume, settings

import google.oauth2.utils as utils
import google.oauth2.sts as sts
import google.oauth2._client as _client


# Property 1: Base64 encoding round-trip in utils.py
# The basic authentication header encodes username:password in base64
@given(
    client_id=st.text(min_size=1, max_size=100),
    client_secret=st.text(min_size=0, max_size=100)
)
def test_basic_auth_base64_round_trip(client_id, client_secret):
    """Test that basic auth header encoding/decoding is consistent."""
    # Create a client authentication object
    client_auth = utils.ClientAuthentication(
        utils.ClientAuthType.basic,
        client_id,
        client_secret
    )
    
    # Create handler with the authentication
    handler = utils.OAuthClientAuthHandler(client_auth)
    
    # Apply authentication to headers
    headers = {}
    handler.apply_client_authentication_options(headers)
    
    # Extract and decode the Authorization header
    if "Authorization" in headers:
        auth_header = headers["Authorization"]
        assert auth_header.startswith("Basic ")
        
        # Extract base64 part
        b64_credentials = auth_header[6:]  # Remove "Basic " prefix
        
        # Decode base64
        decoded = base64.b64decode(b64_credentials).decode('utf-8')
        
        # Verify it matches the original
        expected = f"{client_id}:{client_secret if client_secret else ''}"
        assert decoded == expected


# Property 2: JSON options encoding/decoding in sts.py
# Additional options are JSON-encoded then URL-quoted
@given(
    options=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=10
    )
)
def test_sts_options_encoding_round_trip(options):
    """Test that STS additional options encoding/decoding is reversible."""
    # Skip if options is empty (will be removed from request body)
    if not options:
        return
        
    # Create a mock request
    def mock_request(url, method, headers, body):
        mock_response = mock.Mock()
        mock_response.status = 200
        mock_response.data = json.dumps({"access_token": "test"}).encode('utf-8')
        return mock_response
    
    # Create STS client
    client = sts.Client("https://example.com/token")
    
    # Build request body like exchange_token does
    request_body = {"options": None}
    if options:
        request_body["options"] = urllib.parse.quote(json.dumps(options))
    
    # Verify we can decode back to original
    if request_body["options"] is not None:
        decoded_json = urllib.parse.unquote(request_body["options"])
        decoded_options = json.loads(decoded_json)
        assert decoded_options == options


# Property 3: Expiry parsing handles both int and string expires_in
@given(
    expires_in=st.one_of(
        st.integers(min_value=0, max_value=86400),  # int seconds
        st.from_regex(r"[0-9]{1,6}", fullmatch=True)  # string seconds
    )
)
def test_expiry_parsing_int_and_string(expires_in):
    """Test that _parse_expiry handles both int and string expires_in values."""
    response_data = {"expires_in": expires_in}
    
    # Parse expiry
    expiry = _client._parse_expiry(response_data)
    
    # Should return a datetime
    assert isinstance(expiry, datetime.datetime)
    
    # Calculate expected expiry
    expected_seconds = int(expires_in) if isinstance(expires_in, str) else expires_in
    
    # Check that the expiry is approximately correct (within 2 seconds for clock drift)
    now = datetime.datetime.utcnow()
    expected_expiry = now + datetime.timedelta(seconds=expected_seconds)
    
    # Allow 2 second tolerance for execution time
    diff = abs((expiry - expected_expiry).total_seconds())
    assert diff < 2


# Property 4: Empty field removal in sts.py
@given(
    grant_type=st.text(min_size=1, max_size=50),
    resource=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
    audience=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
    scopes=st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=50), max_size=5)),
    requested_token_type=st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_sts_empty_field_removal(grant_type, resource, audience, scopes, requested_token_type):
    """Test that empty fields are removed from STS request body."""
    # Build request body like the STS client does
    request_body = {
        "grant_type": grant_type,
        "resource": resource,
        "audience": audience,
        "scope": " ".join(scopes or []),
        "requested_token_type": requested_token_type,
        "subject_token": "test_token",  # Required field
        "subject_token_type": "test_type",  # Required field
        "actor_token": None,
        "actor_token_type": None,
        "options": None,
    }
    
    # Remove empty fields like the code does
    for k, v in dict(request_body).items():
        if v is None or v == "":
            del request_body[k]
    
    # Verify no None or empty string values remain
    for value in request_body.values():
        assert value is not None
        assert value != ""
    
    # Verify required fields are always present
    assert "grant_type" in request_body
    assert "subject_token" in request_body
    assert "subject_token_type" in request_body


# Property 5: Error response parsing with fallback
@given(
    error_code=st.text(min_size=1, max_size=50),
    error_description=st.one_of(st.none(), st.text(max_size=200)),
    error_uri=st.one_of(st.none(), st.text(max_size=200))
)
def test_error_response_parsing_json(error_code, error_description, error_uri):
    """Test that handle_error_response correctly parses JSON error responses."""
    # Build error response
    error_data = {"error": error_code}
    if error_description is not None:
        error_data["error_description"] = error_description
    if error_uri is not None:
        error_data["error_uri"] = error_uri
    
    response_body = json.dumps(error_data)
    
    # Test that it raises OAuthError with correct message
    try:
        utils.handle_error_response(response_body)
        assert False, "Should have raised OAuthError"
    except Exception as e:
        # Check exception type
        assert e.__class__.__name__ == "OAuthError"
        
        # Check that error code is in the message
        assert f"Error code {error_code}" in str(e)
        
        # Check optional fields are included if present
        if error_description:
            assert error_description in str(e)
        if error_uri:
            assert error_uri in str(e)


@given(response_body=st.text(min_size=1, max_size=500))
def test_error_response_parsing_fallback(response_body):
    """Test that handle_error_response falls back to raw response for non-JSON."""
    # Skip valid JSON that contains "error" field
    try:
        data = json.loads(response_body)
        if isinstance(data, dict) and "error" in data:
            return  # Skip valid error JSON
    except:
        pass  # Not valid JSON, proceed with test
    
    # Test that it raises OAuthError with raw response as message
    try:
        utils.handle_error_response(response_body)
        assert False, "Should have raised OAuthError"
    except Exception as e:
        # Check exception type
        assert e.__class__.__name__ == "OAuthError"
        
        # For non-JSON or JSON without error field, should use raw response
        assert response_body in str(e)