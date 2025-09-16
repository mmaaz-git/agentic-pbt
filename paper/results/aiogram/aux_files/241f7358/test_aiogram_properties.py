import math
from hypothesis import given, strategies as st, assume, settings
import pytest
from aiogram.utils.deep_linking import encode_payload, decode_payload
from aiogram.utils.text_decorations import add_surrogates, remove_surrogates
from aiogram.utils import markdown


# Test 1: Round-trip property for encode_payload/decode_payload
@given(st.text())
@settings(max_examples=1000)
def test_payload_round_trip(text):
    """Test that decode(encode(x)) == x for payload functions."""
    # According to the docs, these work with URL-safe base64url encoding
    encoded = encode_payload(text)
    decoded = decode_payload(encoded)
    assert decoded == text


# Test 2: Round-trip with custom encoder/decoder
@given(st.text())
@settings(max_examples=500)
def test_payload_round_trip_with_custom_encoder(text):
    """Test round-trip with custom encoder/decoder functions."""
    # Test with a simple XOR cipher as encoder/decoder
    key = 42
    
    def xor_encode(data: bytes) -> bytes:
        return bytes(b ^ key for b in data)
    
    def xor_decode(data: bytes) -> bytes:
        return bytes(b ^ key for b in data)
    
    encoded = encode_payload(text, encoder=xor_encode)
    decoded = decode_payload(encoded, decoder=xor_decode)
    assert decoded == text


# Test 3: Round-trip property for add_surrogates/remove_surrogates
@given(st.text())
@settings(max_examples=1000)
def test_surrogates_round_trip(text):
    """Test that remove_surrogates(add_surrogates(x)) == x."""
    surrogated = add_surrogates(text)
    assert isinstance(surrogated, bytes)
    restored = remove_surrogates(surrogated)
    assert restored == text


# Test 4: Markdown bold function preserves content
@given(st.text(min_size=1))
@settings(max_examples=500)
def test_markdown_bold_preserves_content(text):
    """Test that bold formatting preserves the content."""
    result = markdown.bold(text)
    # Bold markdown uses * around text
    assert text in result
    assert result.startswith('*') and result.endswith('*')


# Test 5: Markdown code function preserves content
@given(st.text(min_size=1))
@settings(max_examples=500)
def test_markdown_code_preserves_content(text):
    """Test that code formatting preserves the content."""
    result = markdown.code(text)
    # Code markdown uses ` around text
    assert text in result
    assert result.startswith('`') and result.endswith('`')


# Test 6: Markdown link function properties
@given(st.text(min_size=1), st.text(min_size=1))
@settings(max_examples=500)
def test_markdown_link_properties(title, url):
    """Test that link formatting includes both title and URL."""
    result = markdown.link(title, url)
    # Markdown link format is [title](url)
    assert title in result
    assert url in result


# Test 7: Multiple arguments to markdown functions
@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
@settings(max_examples=500)
def test_markdown_multiple_args(texts):
    """Test markdown functions with multiple arguments."""
    result = markdown.bold(*texts)
    # All texts should be in the result
    for text in texts:
        assert text in result


# Test 8: HTML markdown functions (h-prefixed)
@given(st.text(min_size=1))
@settings(max_examples=500)
def test_html_markdown_bold(text):
    """Test HTML-style bold formatting."""
    result = markdown.hbold(text)
    # HTML bold uses <b> tags
    assert text in result
    assert result.startswith('<b>') and result.endswith('</b>')


# Test 9: Test empty string handling
@given(st.just(''))
@settings(max_examples=100)
def test_empty_string_payload(text):
    """Test that empty strings are handled correctly in payload functions."""
    encoded = encode_payload(text)
    decoded = decode_payload(encoded)
    assert decoded == text


@given(st.just(''))
@settings(max_examples=100)
def test_empty_string_surrogates(text):
    """Test that empty strings are handled correctly in surrogate functions."""
    surrogated = add_surrogates(text)
    restored = remove_surrogates(surrogated)
    assert restored == text


# Test 10: Unicode handling in payload functions
@given(st.text(alphabet='🦄🎉🌟😀🔥💖✨🎨🌈🍕', min_size=1))
@settings(max_examples=500)
def test_unicode_payload_round_trip(text):
    """Test that Unicode emojis work correctly in payload encoding."""
    encoded = encode_payload(text)
    decoded = decode_payload(encoded)
    assert decoded == text


# Test 11: Unicode handling in surrogate functions
@given(st.text(alphabet='🦄🎉🌟😀🔥💖✨🎨🌈🍕', min_size=1))
@settings(max_examples=500)
def test_unicode_surrogates_round_trip(text):
    """Test that Unicode emojis work correctly in surrogate functions."""
    surrogated = add_surrogates(text)
    restored = remove_surrogates(surrogated)
    assert restored == text


# Test 12: Special characters in markdown
@given(st.text(alphabet='*_`[]()\\', min_size=1))
@settings(max_examples=500)
def test_markdown_special_chars(text):
    """Test that special markdown characters are handled."""
    # These functions should handle special chars somehow
    result_bold = markdown.bold(text)
    result_code = markdown.code(text)
    result_italic = markdown.italic(text)
    
    # The original text should still be findable in the result
    assert text in result_bold
    assert text in result_code
    assert text in result_italic


# Test 13: Blockquote with newlines
@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
@settings(max_examples=500)
def test_markdown_blockquote(texts):
    """Test blockquote formatting with multiple lines."""
    result = markdown.blockquote(*texts)
    # Each text should be in the result
    for text in texts:
        assert text in result
    # Blockquotes use > prefix
    assert '>' in result


# Test 14: Pre-formatted text
@given(st.text(min_size=1))
@settings(max_examples=500)
def test_markdown_pre(text):
    """Test pre-formatted text."""
    result = markdown.pre(text)
    assert text in result
    # Pre uses triple backticks
    assert '```' in result


# Test 15: Hide link function
@given(st.text(min_size=1))
@settings(max_examples=500)
def test_markdown_hide_link(url):
    """Test hide_link function."""
    result = markdown.hide_link(url)
    assert url in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])