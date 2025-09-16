import sys
import unittest.mock as mock
from hypothesis import given, strategies as st, settings, assume
from requests_oauthlib import OAuth1
from oauthlib.oauth1 import SIGNATURE_TYPE_AUTH_HEADER, SIGNATURE_TYPE_BODY, SIGNATURE_TYPE_QUERY


@given(
    signature_type=st.one_of(
        st.just(SIGNATURE_TYPE_AUTH_HEADER),
        st.just(SIGNATURE_TYPE_BODY),
        st.just(SIGNATURE_TYPE_QUERY),
        st.text(min_size=1),
        st.just("auth_header"),
        st.just("body"),
        st.just("query"),
    )
)
def test_signature_type_normalization(signature_type):
    """Test that signature_type is properly normalized to uppercase if it's a string."""
    client_key = "test_key"
    
    oauth = OAuth1(client_key=client_key, signature_type=signature_type)
    
    # The signature_type should be uppercase in the client
    if hasattr(signature_type, 'upper'):
        assert oauth.client.signature_type == signature_type.upper()
    else:
        assert oauth.client.signature_type == signature_type


@given(
    client_key=st.text(min_size=1),
    client_secret=st.text(),
    resource_owner_key=st.text(),
    resource_owner_secret=st.text(),
    force_include_body=st.booleans(),
    content_type=st.one_of(
        st.none(),
        st.just("application/x-www-form-urlencoded"),
        st.just("application/json"),
        st.just("text/plain"),
        st.text(),
    ),
    body=st.one_of(
        st.none(),
        st.text(),
        st.binary(),
        st.just("key=value&other=data"),
    ),
)
def test_force_include_body_property(
    client_key, client_secret, resource_owner_key, 
    resource_owner_secret, force_include_body, content_type, body
):
    """Test that force_include_body always causes body to be included in signing."""
    
    oauth = OAuth1(
        client_key=client_key,
        client_secret=client_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        force_include_body=force_include_body
    )
    
    # Create a mock request object
    request = mock.Mock()
    request.url = "http://example.com/test"
    request.method = "POST"
    request.body = body
    request.headers = {}
    if content_type is not None:
        request.headers["Content-Type"] = content_type
    
    # Mock the client.sign method to track what body was passed
    original_sign = oauth.client.sign
    sign_calls = []
    
    def track_sign(url, method, body, headers):
        sign_calls.append({"url": url, "method": method, "body": body, "headers": headers})
        return original_sign(url, method, body, headers)
    
    oauth.client.sign = track_sign
    request.prepare_headers = mock.Mock()
    
    # Call the OAuth1 handler
    result = oauth(request)
    
    # Check that sign was called
    assert len(sign_calls) == 1
    
    # If force_include_body is True, body should be passed to sign (not None)
    # unless the content type is form-encoded (which has its own logic)
    if force_include_body and "application/x-www-form-urlencoded" not in request.headers.get("Content-Type", ""):
        assert sign_calls[0]["body"] is not None
        if body:
            assert sign_calls[0]["body"] == body
        else:
            assert sign_calls[0]["body"] == ""


@given(
    client_key=st.text(min_size=1),
    non_string_signature_type=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text()),
        st.none(),
    )
)
def test_non_string_signature_type_handling(client_key, non_string_signature_type):
    """Test that non-string signature_type values are handled gracefully."""
    
    # This should not raise an AttributeError even if signature_type doesn't have upper()
    oauth = OAuth1(client_key=client_key, signature_type=non_string_signature_type)
    
    # The signature_type should be passed through unchanged if it doesn't have upper()
    assert oauth.client.signature_type == non_string_signature_type


@given(
    url=st.one_of(
        st.text(min_size=1).filter(lambda x: not x.isspace()),
        st.from_regex(r"https?://[a-z0-9]+\.[a-z]{2,}/[a-z0-9/_-]*", fullmatch=True),
    ),
    method=st.sampled_from(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]),
    body=st.one_of(st.none(), st.text(), st.binary()),
)
def test_url_string_conversion(url, method, body):
    """Test that URLs and methods are properly converted to strings."""
    
    oauth = OAuth1(client_key="test_key")
    
    # Create a mock request with potentially non-string URL/method
    request = mock.Mock()
    request.url = url
    request.method = method
    request.body = body
    request.headers = {}
    request.prepare_headers = mock.Mock()
    
    # Track what gets passed to client.sign
    sign_calls = []
    original_sign = oauth.client.sign
    
    def track_sign(url, method, body, headers):
        sign_calls.append({"url": url, "method": method, "body": body, "headers": headers})
        return (str(url), {}, body)
    
    oauth.client.sign = track_sign
    
    # Call the OAuth1 handler
    result = oauth(request)
    
    # Verify that URL and method were converted to strings
    assert len(sign_calls) == 1
    assert isinstance(sign_calls[0]["url"], str)
    assert isinstance(sign_calls[0]["method"], str)
    assert sign_calls[0]["url"] == str(url)
    assert sign_calls[0]["method"] == str(method)


@given(
    client_key=st.text(min_size=1),
    content_type_header=st.one_of(
        st.none(),
        st.just(""),
        st.just("application/x-www-form-urlencoded"),
        st.just("application/x-www-form-urlencoded; charset=utf-8"),
        st.just("text/plain"),
        st.binary(min_size=1, max_size=100),
    ),
    body_with_params=st.just("key=value&other=data"),
)
def test_content_type_detection_logic(client_key, content_type_header, body_with_params):
    """Test the content type detection and body inclusion logic."""
    
    oauth = OAuth1(client_key=client_key)
    
    request = mock.Mock()
    request.url = "http://example.com"
    request.method = "POST"
    request.body = body_with_params
    request.headers = {}
    
    if content_type_header is not None:
        request.headers["Content-Type"] = content_type_header
    
    request.prepare_headers = mock.Mock()
    
    # Track what happens
    sign_calls = []
    original_sign = oauth.client.sign
    
    def track_sign(url, method, body, headers):
        sign_calls.append({"body": body})
        return (url, {}, body)
    
    oauth.client.sign = track_sign
    
    result = oauth(request)
    
    # If content type is empty/missing AND body has URL params, 
    # it should be treated as form-urlencoded
    if not content_type_header:
        # When no content type and body has params, should set form-urlencoded
        assert request.headers.get("Content-Type") == "application/x-www-form-urlencoded"
        assert sign_calls[0]["body"] == body_with_params
    elif isinstance(content_type_header, bytes):
        # Bytes should be decoded to string
        content_str = content_type_header.decode('utf-8')
        if "application/x-www-form-urlencoded" in content_str:
            assert sign_calls[0]["body"] == body_with_params
    elif "application/x-www-form-urlencoded" in str(content_type_header):
        # Form-encoded should include body
        assert sign_calls[0]["body"] == body_with_params
    else:
        # Non-form-encoded should not include body
        assert sign_calls[0]["body"] is None


if __name__ == "__main__":
    # Run tests
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))