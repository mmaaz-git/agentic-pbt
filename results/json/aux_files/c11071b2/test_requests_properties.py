import math
from collections import OrderedDict
from http.cookiejar import CookieJar
import string

import pytest
from hypothesis import assume, given, strategies as st, settings

import requests.utils


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_dict_to_key_val_list_round_trip(d):
    """Test that converting dict to key-val list and back preserves data."""
    result = requests.utils.to_key_val_list(d)
    assert isinstance(result, list)
    
    reconstructed = requests.utils.from_key_val_list(result)
    assert isinstance(reconstructed, OrderedDict)
    
    # Check that all keys and values are preserved
    assert dict(reconstructed) == d


@given(st.lists(st.tuples(st.text(min_size=1), st.text())))
def test_list_to_key_val_round_trip(lst):
    """Test round-trip for list of tuples through from/to_key_val_list."""
    # from_key_val_list expects valid key-value pairs
    result = requests.utils.from_key_val_list(lst)
    assert isinstance(result, OrderedDict)
    
    back = requests.utils.to_key_val_list(result)
    assert isinstance(back, list)
    
    # Should preserve the key-value pairs (though possibly deduplicated)
    # OrderedDict will keep only the last value for duplicate keys
    expected = OrderedDict(lst)
    assert OrderedDict(back) == expected


@given(st.text())
def test_unquote_unreserved_idempotent(uri):
    """Test that unquote_unreserved is idempotent."""
    # First application
    try:
        result1 = requests.utils.unquote_unreserved(uri)
        # Second application should give same result (idempotence)
        result2 = requests.utils.unquote_unreserved(result1)
        assert result1 == result2
    except requests.exceptions.InvalidURL:
        # If it raises an exception, that's fine - we're testing the property
        # for valid inputs
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits + "-._~"))
def test_unquote_unreserved_preserves_unreserved(text):
    """Test that unreserved characters are preserved by unquote_unreserved."""
    # These characters should pass through unchanged
    result = requests.utils.unquote_unreserved(text)
    assert result == text


@given(st.dictionaries(
    st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_-"),
    st.text(alphabet=string.printable)
))
def test_cookiejar_round_trip(cookie_dict):
    """Test round-trip conversion between dict and CookieJar."""
    # Convert dict to cookiejar
    jar = requests.utils.cookiejar_from_dict(cookie_dict)
    assert isinstance(jar, CookieJar)
    
    # Convert back to dict
    result_dict = requests.utils.dict_from_cookiejar(jar)
    
    # Should preserve all cookies
    assert result_dict == cookie_dict


@given(st.text())
def test_requote_uri_idempotent(uri):
    """Test that requote_uri is idempotent."""
    try:
        result1 = requests.utils.requote_uri(uri)
        result2 = requests.utils.requote_uri(result1)
        assert result1 == result2
    except (requests.exceptions.InvalidURL, UnicodeError, KeyError):
        # Some inputs might cause exceptions, that's fine
        pass


@given(st.lists(st.tuples(
    st.text(min_size=1, alphabet=string.ascii_letters),
    st.one_of(st.none(), st.text())
)))
def test_parse_header_links_structure(links_data):
    """Test parse_header_links with generated link headers."""
    # Build a link header string
    link_parts = []
    for url, rel in links_data:
        if rel is not None:
            link_parts.append(f'<{url}>; rel="{rel}"')
        else:
            link_parts.append(f'<{url}>')
    
    header_value = ', '.join(link_parts)
    
    try:
        result = requests.utils.parse_header_links(header_value)
        
        # Result should be a list of dictionaries
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert 'url' in item
            
        # Number of results should match input (if valid)
        if link_parts:
            assert len(result) == len(link_parts)
    except (ValueError, AttributeError):
        # Some malformed inputs might cause exceptions
        pass


@given(st.text(min_size=1))
def test_super_len_non_negative(obj):
    """Test that super_len always returns non-negative values."""
    try:
        length = requests.utils.super_len(obj)
        assert length >= 0
    except (TypeError, AttributeError, UnicodeError):
        # Some objects might not have a length
        pass


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_dict_to_sequence_preserves_items(d):
    """Test dict_to_sequence preserves all items."""
    result = requests.utils.dict_to_sequence(d)
    # Should be iterable
    result_list = list(result)
    
    # Should preserve all key-value pairs
    assert len(result_list) == len(d)
    for key, value in result_list:
        assert key in d
        assert d[key] == value


# Test quote/unquote round-trip with constrained input
@given(st.text(alphabet=string.ascii_letters + string.digits + " "))
def test_quote_unquote_round_trip(text):
    """Test that quote and unquote are inverses for simple text."""
    # Quote the text
    quoted = requests.utils.quote(text)
    # Unquote should recover original
    unquoted = requests.utils.unquote(quoted)
    assert unquoted == text


# Test for potential edge cases in unquote_unreserved
@given(st.text())
def test_unquote_unreserved_percent_handling(text):
    """Test that unquote_unreserved handles percent signs correctly."""
    # Add some percent signs that aren't valid escape sequences
    test_input = text + "%"
    result = requests.utils.unquote_unreserved(test_input)
    # Should handle trailing percent
    assert "%" in result or result == text


@given(st.text(alphabet="%" + string.hexdigits))
def test_unquote_unreserved_hex_sequences(text):
    """Test unquote_unreserved with various hex-like sequences."""
    try:
        result = requests.utils.unquote_unreserved(text)
        # If it succeeds, check idempotence
        result2 = requests.utils.unquote_unreserved(result)
        assert result == result2
    except requests.exceptions.InvalidURL as e:
        # Check that the error message is informative
        assert "Invalid percent-escape sequence" in str(e)


if __name__ == "__main__":
    # Run a quick test to see if anything fails
    import sys
    pytest.main([__file__, "-v", "--tb=short"])