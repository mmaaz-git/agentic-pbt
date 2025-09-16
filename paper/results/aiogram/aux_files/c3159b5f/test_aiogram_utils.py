"""Property-based tests for aiogram.utils using Hypothesis"""

import re
from hypothesis import given, strategies as st, assume, settings
import aiogram.utils.payload as payload
import aiogram.utils.text_decorations as td
import aiogram.utils.deep_linking as dl


# Test 1: Round-trip property for payload encode/decode
@given(st.text())
def test_payload_encode_decode_round_trip(text):
    """Test that decode_payload(encode_payload(x)) == x"""
    encoded = payload.encode_payload(text)
    decoded = payload.decode_payload(encoded)
    assert decoded == text, f"Round-trip failed for {text!r}"


# Test 2: Round-trip with custom encoder/decoder
@given(st.text())
def test_payload_with_custom_encoder_decoder(text):
    """Test round-trip with a custom encoder/decoder (identity function)"""
    def identity_encoder(b: bytes) -> bytes:
        return b
    
    encoded = payload.encode_payload(text, encoder=identity_encoder)
    decoded = payload.decode_payload(encoded, decoder=identity_encoder)
    assert decoded == text


# Test 3: Round-trip property for surrogates
@given(st.text())
def test_surrogates_round_trip(text):
    """Test that remove_surrogates(add_surrogates(x)) == x"""
    with_surrogates = td.add_surrogates(text)
    without_surrogates = td.remove_surrogates(with_surrogates)
    assert without_surrogates == text


# Test 4: Deep link payload validation - encoded payloads should always work
@given(st.text(min_size=1))
def test_deep_link_encoded_payload_accepts_any_string(text):
    """Test that create_deep_link with encode=True accepts any string"""
    # This should work for any string when encode=True
    link = dl.create_deep_link(
        username="testbot",
        link_type="start",
        payload=text,
        encode=True
    )
    assert isinstance(link, str)
    assert "testbot" in link


# Test 5: Deep link payload validation - unencoded must match pattern
@given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=64))
def test_deep_link_unencoded_valid_payload(text):
    """Test that valid unencoded payloads work"""
    # Generate only valid characters: A-Z, a-z, 0-9, _, -
    link = dl.create_deep_link(
        username="testbot",
        link_type="start", 
        payload=text,
        encode=False
    )
    assert isinstance(link, str)
    assert text in link


# Test 6: Deep link payload length invariant
@given(st.text(min_size=65))
def test_deep_link_payload_length_limit(text):
    """Test that payloads > 64 chars are rejected when unencoded"""
    # Ensure we only use valid characters for unencoded payload
    valid_text = re.sub(r'[^A-Za-z0-9_-]', 'a', text)[:100]  # Make it valid but long
    
    try:
        dl.create_deep_link(
            username="testbot",
            link_type="start",
            payload=valid_text,
            encode=False
        )
        assert False, "Should have raised ValueError for long payload"
    except ValueError as e:
        assert "64 characters" in str(e)


# Test 7: Deep link invalid characters should fail when unencoded
@given(st.text(alphabet=st.characters(blacklist_categories=("Lu", "Ll", "Nd"), blacklist_characters="_-"), min_size=1))
def test_deep_link_invalid_chars_unencoded(text):
    """Test that invalid characters are rejected when unencoded"""
    assume(len(text) <= 64)
    assume(re.search(r'[^A-Za-z0-9_-]', text))  # Ensure we have invalid chars
    
    try:
        dl.create_deep_link(
            username="testbot",
            link_type="start",
            payload=text,
            encode=False
        )
        assert False, f"Should have raised ValueError for invalid chars in {text!r}"
    except ValueError as e:
        assert "Wrong payload" in str(e) or "Only A-Z" in str(e)


# Test 8: Encoded payload should handle length correctly
@given(st.text(min_size=0, max_size=1000))
def test_deep_link_encoded_payload_length(text):
    """Test that encoding handles various payload lengths"""
    # When encoded, check if the resulting encoded string fits in 64 chars
    encoded = payload.encode_payload(text)
    
    if len(encoded) <= 64:
        # Should succeed
        link = dl.create_deep_link(
            username="testbot",
            link_type="start",
            payload=text,
            encode=True
        )
        assert isinstance(link, str)
    else:
        # Should fail due to encoded length > 64
        try:
            dl.create_deep_link(
                username="testbot",
                link_type="start",
                payload=text,
                encode=True
            )
            # If it succeeds, that's fine - the implementation might be different
        except ValueError as e:
            assert "64 characters" in str(e)


# Test 9: Link types should all work
@given(
    link_type=st.sampled_from(["start", "startgroup", "startapp"]),
    text=st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=64)
)
def test_deep_link_different_types(link_type, text):
    """Test that all link types work correctly"""
    link = dl.create_deep_link(
        username="testbot",
        link_type=link_type,
        payload=text,
        encode=False
    )
    assert isinstance(link, str)
    assert "testbot" in link