#!/usr/bin/env python3
"""Property-based tests for google.auth module using Hypothesis."""

import sys
import json
import base64
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the modules we're testing
from google.auth import _helpers
from google.auth import jwt


# Strategy for valid unicode strings
valid_unicode = st.text(min_size=1)

# Strategy for valid bytes
valid_bytes = st.binary(min_size=1)

# Strategy for non-empty scope lists  
valid_scopes = st.lists(
    st.text(alphabet=st.characters(blacklist_characters=' \t\n\r'), min_size=1),
    min_size=1,
    unique=True
)

# Strategy for URLs with query params
urls_with_params = st.builds(
    lambda base, params: (base, params),
    base=st.sampled_from([
        "http://example.com",
        "https://example.com/path",
        "http://example.com?existing=param",
        "https://example.com/path?a=1&b=2"
    ]),
    params=st.dictionaries(
        st.text(alphabet=st.characters(blacklist_characters='&=?#'), min_size=1),
        st.text(min_size=0),
        min_size=0,
        max_size=5
    )
)


@given(valid_unicode)
@settings(max_examples=1000)
def test_to_bytes_from_bytes_round_trip(text):
    """Test that from_bytes(to_bytes(s)) == s for any string."""
    # Convert string to bytes
    as_bytes = _helpers.to_bytes(text)
    
    # Convert back to string
    back_to_string = _helpers.from_bytes(as_bytes)
    
    # Should get original string back
    assert back_to_string == text
    assert isinstance(as_bytes, bytes)
    assert isinstance(back_to_string, str)


@given(valid_bytes)
@settings(max_examples=1000)
def test_from_bytes_to_bytes_round_trip(data):
    """Test that to_bytes(from_bytes(b)) == b for any bytes."""
    # Convert bytes to string
    as_string = _helpers.from_bytes(data)
    
    # Convert back to bytes
    back_to_bytes = _helpers.to_bytes(as_string)
    
    # Should get original bytes back
    assert back_to_bytes == data
    assert isinstance(as_string, str)
    assert isinstance(back_to_bytes, bytes)


@given(valid_bytes)
@settings(max_examples=1000)
def test_base64_encode_decode_round_trip(data):
    """Test that padded_urlsafe_b64decode(unpadded_urlsafe_b64encode(b)) == b."""
    # Encode without padding
    encoded = _helpers.unpadded_urlsafe_b64encode(data)
    
    # Decode with padding support
    decoded = _helpers.padded_urlsafe_b64decode(encoded)
    
    # Should get original bytes back
    assert decoded == data
    assert isinstance(encoded, bytes)
    assert isinstance(decoded, bytes)


@given(valid_scopes)
@settings(max_examples=1000)
def test_scopes_round_trip(scopes):
    """Test that string_to_scopes(scopes_to_string(scopes)) == scopes."""
    # Convert list to string
    as_string = _helpers.scopes_to_string(scopes)
    
    # Convert back to list
    back_to_list = _helpers.string_to_scopes(as_string)
    
    # Should get original list back
    assert back_to_list == scopes
    assert isinstance(as_string, str)
    assert isinstance(back_to_list, list)


@given(urls_with_params)
@settings(max_examples=500)
def test_update_query_idempotence(url_and_params):
    """Test that update_query is idempotent: f(f(x)) == f(x)."""
    url, params = url_and_params
    
    # Skip if params is empty - nothing to test
    if not params:
        return
    
    # Apply update once
    updated_once = _helpers.update_query(url, params)
    
    # Apply update again with same params
    updated_twice = _helpers.update_query(updated_once, params)
    
    # Should be the same (idempotent)
    assert updated_once == updated_twice


@given(st.dictionaries(
    st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cf')), min_size=1),
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none()
    )
))
@settings(max_examples=500)
def test_jwt_segment_decode_encode_round_trip(data):
    """Test that _decode_jwt_segment can decode what we encode."""
    # Skip if data can't be JSON serialized
    try:
        json_str = json.dumps(data)
    except (TypeError, ValueError):
        assume(False)
    
    # Encode the data like JWT segments are encoded
    encoded = _helpers.unpadded_urlsafe_b64encode(json_str.encode('utf-8'))
    
    # Decode using JWT segment decoder
    decoded = jwt._decode_jwt_segment(encoded)
    
    # Should get original data back
    assert decoded == data


@given(st.text(min_size=1))
@settings(max_examples=500)
def test_parse_content_type_never_crashes(content_type):
    """Test that parse_content_type never crashes on any input."""
    # This should never raise an exception
    result = _helpers.parse_content_type(content_type)
    
    # Should always return a string
    assert isinstance(result, str)
    
    # Should be lowercase
    assert result == result.lower()


@given(st.lists(st.text(), min_size=0))
@settings(max_examples=500)
def test_scopes_empty_list_handling(scopes):
    """Test that empty scopes are handled correctly."""
    if not scopes or all(not s for s in scopes):
        # Empty or all-empty strings should become empty string
        result = _helpers.scopes_to_string(scopes)
        back = _helpers.string_to_scopes(result)
        # Empty string should convert back to empty list
        if result == "":
            assert back == []
        else:
            # Non-empty result should preserve structure
            assert len(back) == len([s for s in scopes if s])


@given(st.binary(min_size=0, max_size=1000))
@settings(max_examples=500)
def test_base64_decode_encoded_has_no_padding(data):
    """Test that unpadded_urlsafe_b64encode really removes padding."""
    encoded = _helpers.unpadded_urlsafe_b64encode(data)
    
    # Should not end with padding characters
    assert not encoded.endswith(b'=')
    assert not encoded.endswith(b'==')
    
    # Should still be valid base64 (decodeable)
    decoded = _helpers.padded_urlsafe_b64decode(encoded)
    assert decoded == data


if __name__ == "__main__":
    # Run a quick test to verify imports work
    print("Testing google.auth property-based tests...")
    test_to_bytes_from_bytes_round_trip("test")
    test_base64_encode_decode_round_trip(b"test")
    test_scopes_round_trip(["scope1", "scope2"])
    print("Basic tests passed. Run with pytest for full suite.")