#!/usr/bin/env python3
"""Property-based tests for cloudscraper.cloudflare module."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
from cloudscraper.cloudflare import Cloudflare


# Test 1: Robustness - unescape should handle any string without crashing
@given(st.text())
@settings(max_examples=1000)
def test_unescape_robustness(text):
    """Test that unescape handles any string input without crashing."""
    try:
        result = Cloudflare.unescape(text)
        assert isinstance(result, str)
    except Exception as e:
        # If it crashes on valid string input, that's a bug
        raise AssertionError(f"unescape crashed on input {repr(text)}: {e}")


# Test 2: Preservation - plain text without HTML entities should remain unchanged
@given(st.text(alphabet=st.characters(blacklist_characters="&<>\"'")))
@settings(max_examples=500)
def test_unescape_preserves_plain_text(text):
    """Test that plain text without HTML entities remains unchanged."""
    # Skip if the text accidentally contains entity-like patterns
    assume("&" not in text)
    assume("<" not in text)
    assume(">" not in text)
    
    result = Cloudflare.unescape(text)
    assert result == text, f"Plain text changed: {repr(text)} -> {repr(result)}"


# Test 3: Common entities correctness
@given(
    prefix=st.text(max_size=50),
    entity=st.sampled_from(["&lt;", "&gt;", "&amp;", "&quot;", "&#39;", "&#x27;"]),
    suffix=st.text(max_size=50)
)
@settings(max_examples=500)
def test_unescape_common_entities(prefix, entity, suffix):
    """Test that common HTML entities are correctly unescaped."""
    text = prefix + entity + suffix
    result = Cloudflare.unescape(text)
    
    # Map entities to their unescaped forms
    entity_map = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&quot;": '"',
        "&#39;": "'",
        "&#x27;": "'"
    }
    
    expected = prefix + entity_map[entity] + suffix
    assert result == expected, f"Entity not properly unescaped: {repr(text)} -> {repr(result)}, expected {repr(expected)}"


# Test 4: Multiple entities in one string
@given(
    st.lists(
        st.tuples(
            st.text(max_size=10),
            st.sampled_from(["&lt;", "&gt;", "&amp;", "&quot;", "&#39;"])
        ),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=500)
def test_unescape_multiple_entities(segments):
    """Test that multiple HTML entities in one string are all unescaped."""
    # Build a string with alternating text and entities
    parts = []
    for text, entity in segments:
        parts.append(text)
        parts.append(entity)
    text = "".join(parts)
    
    result = Cloudflare.unescape(text)
    
    # Check that all entities were unescaped
    assert "&lt;" not in result or "&amp;lt;" in text  # Unless it was double-escaped
    assert "&gt;" not in result or "&amp;gt;" in text
    assert "&amp;" not in result or "&amp;amp;" in text
    assert "&quot;" not in result or "&amp;quot;" in text
    assert "&#39;" not in result or "&amp;#39;" in text


# Test 5: Numeric character references
@given(
    prefix=st.text(max_size=20),
    char_code=st.integers(min_value=32, max_value=126),  # Printable ASCII range
    suffix=st.text(max_size=20)
)
@settings(max_examples=500)
def test_unescape_numeric_entities(prefix, char_code, suffix):
    """Test that numeric character references are correctly unescaped."""
    # Create both decimal and hex forms
    decimal_entity = f"&#{char_code};"
    hex_entity = f"&#x{char_code:x};"
    
    # Test decimal form
    text_decimal = prefix + decimal_entity + suffix
    result_decimal = Cloudflare.unescape(text_decimal)
    expected_char = chr(char_code)
    expected = prefix + expected_char + suffix
    assert result_decimal == expected, f"Decimal entity not properly unescaped: {repr(text_decimal)} -> {repr(result_decimal)}"
    
    # Test hex form
    text_hex = prefix + hex_entity + suffix
    result_hex = Cloudflare.unescape(text_hex)
    assert result_hex == expected, f"Hex entity not properly unescaped: {repr(text_hex)} -> {repr(result_hex)}"


# Test 6: Empty and whitespace strings
@given(st.sampled_from(["", " ", "  ", "\t", "\n", " \t\n "]))
def test_unescape_empty_and_whitespace(text):
    """Test that empty and whitespace strings are handled correctly."""
    result = Cloudflare.unescape(text)
    assert result == text, f"Whitespace not preserved: {repr(text)} -> {repr(result)}"


# Test 7: Very long strings with entities
@given(
    repeat_count=st.integers(min_value=100, max_value=1000),
    entity=st.sampled_from(["&lt;", "&gt;", "&amp;"])
)
@settings(max_examples=50)
def test_unescape_long_strings(repeat_count, entity):
    """Test that unescape handles very long strings with many entities."""
    text = entity * repeat_count
    result = Cloudflare.unescape(text)
    
    entity_map = {"&lt;": "<", "&gt;": ">", "&amp;": "&"}
    expected = entity_map[entity] * repeat_count
    assert result == expected, f"Long string not properly unescaped: {repeat_count} repetitions of {entity}"


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])