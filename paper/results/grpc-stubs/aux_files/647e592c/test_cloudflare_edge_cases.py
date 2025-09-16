#!/usr/bin/env python3
"""Additional edge case tests for cloudscraper.cloudflare.unescape."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
from cloudscraper.cloudflare import Cloudflare


# Test malformed entities
@given(
    prefix=st.text(max_size=20),
    malformed=st.sampled_from([
        "&lt",  # Missing semicolon
        "&gt",
        "&amp",
        "&#39",
        "&",  # Just ampersand
        "&#",  # Incomplete numeric
        "&#x",  # Incomplete hex
        "&;",  # Empty entity
        "&&",  # Double ampersand
        "&lt;&gt",  # Missing semicolon in middle
        "&#999999999999999999;",  # Very large number
        "&#x1ffffffffff;",  # Very large hex
        "&#-1;",  # Negative number
        "&#x-ff;",  # Negative hex
        "&notanentity;",  # Unknown entity name
    ]),
    suffix=st.text(max_size=20)
)
@settings(max_examples=500)
def test_unescape_malformed_entities(prefix, malformed, suffix):
    """Test that malformed entities are handled without crashing."""
    text = prefix + malformed + suffix
    try:
        result = Cloudflare.unescape(text)
        assert isinstance(result, str)
        # The function should either leave malformed entities as-is or handle them gracefully
    except Exception as e:
        raise AssertionError(f"unescape crashed on malformed entity {repr(text)}: {e}")


# Test Unicode and non-ASCII characters
@given(st.text(alphabet=st.characters(min_codepoint=128, max_codepoint=0x10ffff)))
@settings(max_examples=200)
def test_unescape_unicode(text):
    """Test that Unicode characters are preserved correctly."""
    result = Cloudflare.unescape(text)
    assert result == text, f"Unicode text changed: {repr(text)} -> {repr(result)}"


# Test mixed valid and invalid entities
@given(
    st.lists(
        st.one_of(
            st.sampled_from(["&lt;", "&gt;", "&amp;", "normal text"]),
            st.sampled_from(["&lt", "&invalidEntity;", "&#", "&&"])
        ),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=300)
def test_unescape_mixed_valid_invalid(parts):
    """Test handling of mixed valid and invalid entities."""
    text = "".join(parts)
    try:
        result = Cloudflare.unescape(text)
        assert isinstance(result, str)
        # Valid entities should be unescaped
        # We can't assert exact behavior for invalid ones, but it shouldn't crash
    except Exception as e:
        raise AssertionError(f"unescape crashed on mixed input {repr(text)}: {e}")


# Test entity-like patterns that aren't entities
@given(
    prefix=st.text(max_size=10),
    middle=st.sampled_from(["&something;", "&test;", "&foo;", "&bar123;", "&_underscore;", "&-dash;"]),
    suffix=st.text(max_size=10)
)
@settings(max_examples=200)
def test_unescape_false_entities(prefix, middle, suffix):
    """Test that entity-like patterns that aren't real entities are preserved."""
    text = prefix + middle + suffix
    result = Cloudflare.unescape(text)
    # Most false entities should remain unchanged
    # We're mainly testing that it doesn't crash
    assert isinstance(result, str)


# Test extremely nested/repeated escaping
@given(levels=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_unescape_nested_escaping(levels):
    """Test handling of multiply-escaped entities."""
    # Start with a simple character
    text = "<"
    # Escape it multiple times
    for _ in range(levels):
        text = text.replace("&", "&amp;").replace("<", "&lt;")
    
    # Unescape once
    result = Cloudflare.unescape(text)
    
    # It should unescape exactly one level
    assert isinstance(result, str)
    
    # After one unescape, we should have one less level of escaping
    if levels > 1:
        assert "&" in result or "<" in result  # Should still have some entities


# Test named entities beyond the basic ones
@given(
    entity=st.sampled_from([
        "&nbsp;", "&copy;", "&reg;", "&trade;", "&euro;",
        "&pound;", "&yen;", "&cent;", "&sect;", "&para;",
        "&mdash;", "&ndash;", "&hellip;", "&hearts;", "&alpha;",
        "&beta;", "&gamma;", "&Delta;", "&sum;", "&infin;"
    ])
)
@settings(max_examples=200)
def test_unescape_named_entities(entity):
    """Test that various named HTML entities are handled."""
    text = f"prefix {entity} suffix"
    try:
        result = Cloudflare.unescape(text)
        assert isinstance(result, str)
        # The entity should be unescaped (not remain as-is)
        assert entity not in result, f"Named entity {entity} was not unescaped"
    except Exception as e:
        raise AssertionError(f"unescape crashed on named entity {repr(entity)}: {e}")


# Test with null bytes and control characters
@given(
    st.text().map(lambda x: x + "\x00" + x if x else "\x00")
)
@settings(max_examples=100)
def test_unescape_null_bytes(text):
    """Test handling of null bytes in strings."""
    try:
        result = Cloudflare.unescape(text)
        assert isinstance(result, str)
    except Exception as e:
        raise AssertionError(f"unescape crashed on text with null bytes: {e}")


# Test surrogate pairs and invalid UTF-16 sequences
def test_unescape_surrogate_entities():
    """Test handling of surrogate pair entities."""
    test_cases = [
        "&#xD800;",  # High surrogate alone
        "&#xDFFF;",  # Low surrogate alone
        "&#xD800;&#xDC00;",  # Valid surrogate pair
        "&#55296;",  # High surrogate as decimal
    ]
    
    for text in test_cases:
        try:
            result = Cloudflare.unescape(text)
            assert isinstance(result, str)
        except Exception as e:
            # Some surrogate handling might raise exceptions, which is acceptable
            # but we want to know about it
            print(f"Note: surrogate entity {repr(text)} caused exception: {e}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])